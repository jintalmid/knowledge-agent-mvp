import hashlib
from datetime import UTC, datetime
from pathlib import Path
from sqlite3 import Connection, IntegrityError, Row
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.auth import CurrentUser
from app.core.config import get_settings
from app.models.file import FileRole, PipelineStatus
from app.schemas.file import PhysicalFileRead, TaskFileRead
from app.services import parsing as parsing_service
from app.services.tasks import get_task

ALLOWED_FILE_EXTENSIONS = {f".{extension}" for extension in parsing_service.SUPPORTED_FILE_EXTENSIONS}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _physical_row_to_read(row: Row) -> PhysicalFileRead:
    return PhysicalFileRead(**dict(row))


def _task_file_row_to_read(row: Row) -> TaskFileRead:
    data = dict(row)
    data["reused_existing_file"] = data["physical_created_at"] != data["created_at"]
    data.pop("physical_created_at", None)
    return TaskFileRead(**data)


def _normalize_filename(filename: str | None) -> str:
    if not filename:
        return "uploaded_file"
    return Path(filename).name


def _validate_file_extension(filename: str) -> str:
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_FILE_EXTENSIONS:
        allowed = ", ".join(sorted(ext.lstrip(".") for ext in ALLOWED_FILE_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported file type, allowed: {allowed}",
        )
    return file_ext.lstrip(".")


def _get_physical_file_by_hash(connection: Connection, content_hash: str) -> PhysicalFileRead | None:
    row = connection.execute(
        "SELECT * FROM physical_files WHERE content_hash = ?",
        (content_hash,),
    ).fetchone()
    if row is None:
        return None
    return _physical_row_to_read(row)


def get_physical_file(connection: Connection, physical_file_id: str) -> PhysicalFileRead | None:
    row = connection.execute(
        "SELECT * FROM physical_files WHERE id = ?",
        (physical_file_id,),
    ).fetchone()
    if row is None:
        return None
    return _physical_row_to_read(row)


def _get_task_file_by_task_and_physical_file(
    connection: Connection,
    task_id: str,
    physical_file_id: str,
) -> TaskFileRead | None:
    row = connection.execute(
        """
        SELECT
            tf.*,
            pf.file_ext,
            pf.mime_type,
            pf.file_size,
            pf.ref_count,
            pf.created_at AS physical_created_at
        FROM task_files tf
        JOIN physical_files pf ON pf.id = tf.physical_file_id
        WHERE tf.task_id = ? AND tf.physical_file_id = ?
        ORDER BY tf.created_at ASC
        LIMIT 1
        """,
        (task_id, physical_file_id),
    ).fetchone()
    if row is None:
        return None
    return _task_file_row_to_read(row)


async def create_task_file(
    connection: Connection,
    task_id: str,
    upload_file: UploadFile,
    current_user: CurrentUser,
) -> TaskFileRead:
    task = get_task(connection, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")

    original_filename = _normalize_filename(upload_file.filename)
    file_ext = _validate_file_extension(original_filename)
    content = await upload_file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file is empty")

    now = _now_iso()
    content_hash = hashlib.sha256(content).hexdigest()
    physical_file = _get_physical_file_by_hash(connection, content_hash)

    if physical_file is None:
        physical_file_id = f"pf_{uuid4().hex}"
        upload_dir = get_settings().uploads_dir / content_hash
        upload_dir.mkdir(parents=True, exist_ok=True)
        storage_path = upload_dir / f"{content_hash}.{file_ext}"
        storage_path.write_bytes(content)
        try:
            connection.execute(
                """
                INSERT INTO physical_files (
                    id,
                    content_hash,
                    original_filename,
                    file_ext,
                    mime_type,
                    file_size,
                    storage_path,
                    ref_count,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    physical_file_id,
                    content_hash,
                    original_filename,
                    file_ext,
                    upload_file.content_type or "application/octet-stream",
                    len(content),
                    str(storage_path),
                    0,
                    now,
                    now,
                ),
            )
        except IntegrityError:
            physical_file = _get_physical_file_by_hash(connection, content_hash)
            if physical_file is None:
                raise
            physical_file_id = physical_file.id
    else:
        physical_file_id = physical_file.id

    existing_task_file = _get_task_file_by_task_and_physical_file(connection, task_id, physical_file_id)
    if existing_task_file is not None:
        return existing_task_file

    task_file_id = f"tf_{uuid4().hex}"
    try:
        connection.execute(
            """
            INSERT INTO task_files (
                id,
                task_id,
                physical_file_id,
                display_name,
                file_role,
                parse_status,
                parse_error,
                summary_status,
                embedding_status,
                owner_user_id,
                department_id,
                security_level,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_file_id,
                task_id,
                physical_file_id,
                original_filename,
                FileRole.SOURCE.value,
                PipelineStatus.PENDING.value,
                None,
                PipelineStatus.NOT_STARTED.value,
                PipelineStatus.NOT_STARTED.value,
                current_user.owner_user_id,
                current_user.department_id,
                current_user.security_level,
                now,
                now,
            ),
        )
    except IntegrityError:
        existing_task_file = _get_task_file_by_task_and_physical_file(connection, task_id, physical_file_id)
        if existing_task_file is not None:
            return existing_task_file
        raise
    connection.execute(
        """
        UPDATE physical_files
        SET ref_count = ref_count + 1, updated_at = ?
        WHERE id = ?
        """,
        (now, physical_file_id),
    )
    task_file = get_task_file(connection, task_file_id)
    if task_file is None:
        raise HTTPException(status_code=500, detail="failed to create task file")

    try:
        parsing_service.parse_task_file(connection, task_file_id)
    except HTTPException as exc:
        parsing_service.set_parse_status(connection, task_file_id, "failed", str(exc.detail))
    except Exception as exc:
        parsing_service.set_parse_status(connection, task_file_id, "failed", f"parse failed: {exc}")

    refreshed_task_file = get_task_file(connection, task_file_id)
    if refreshed_task_file is None:
        raise HTTPException(status_code=500, detail="failed to load task file after parse")
    return refreshed_task_file


def list_task_files(connection: Connection, task_id: str) -> list[TaskFileRead] | None:
    task = get_task(connection, task_id)
    if task is None:
        return None

    rows = connection.execute(
        """
        SELECT
            tf.*,
            pf.file_ext,
            pf.mime_type,
            pf.file_size,
            pf.ref_count,
            pf.created_at AS physical_created_at
        FROM task_files tf
        JOIN physical_files pf ON pf.id = tf.physical_file_id
        WHERE tf.task_id = ?
        ORDER BY tf.created_at DESC
        """,
        (task_id,),
    ).fetchall()
    return [_task_file_row_to_read(row) for row in rows]


def get_task_file(connection: Connection, task_file_id: str) -> TaskFileRead | None:
    row = connection.execute(
        """
        SELECT
            tf.*,
            pf.file_ext,
            pf.mime_type,
            pf.file_size,
            pf.ref_count,
            pf.created_at AS physical_created_at
        FROM task_files tf
        JOIN physical_files pf ON pf.id = tf.physical_file_id
        WHERE tf.id = ?
        """,
        (task_file_id,),
    ).fetchone()
    if row is None:
        return None
    return _task_file_row_to_read(row)


def delete_task_file(connection: Connection, task_file_id: str) -> bool:
    task_file = get_task_file(connection, task_file_id)
    if task_file is None:
        return False

    now = _now_iso()
    connection.execute("DELETE FROM task_files WHERE id = ?", (task_file_id,))
    connection.execute(
        """
        UPDATE physical_files
        SET ref_count = MAX(ref_count - 1, 0), updated_at = ?
        WHERE id = ?
        """,
        (now, task_file.physical_file_id),
    )
    return True
