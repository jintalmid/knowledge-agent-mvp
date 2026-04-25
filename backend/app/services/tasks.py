from datetime import UTC, datetime
from sqlite3 import Connection, Row
from uuid import uuid4

from app.core.auth import CurrentUser
from app.models.task import TaskStatus
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _row_to_task(row: Row) -> TaskRead:
    return TaskRead(**dict(row))


def create_task(connection: Connection, payload: TaskCreate, current_user: CurrentUser) -> TaskRead:
    now = _now_iso()
    task_id = f"task_{uuid4().hex}"
    connection.execute(
        """
        INSERT INTO tasks (
            id,
            name,
            description,
            status,
            owner_user_id,
            department_id,
            security_level,
            knowledge_base_id,
            template_id,
            iteration_count,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            payload.name,
            payload.description,
            TaskStatus.DRAFT.value,
            current_user.owner_user_id,
            current_user.department_id,
            current_user.security_level,
            payload.knowledge_base_id,
            payload.template_id,
            0,
            now,
            now,
        ),
    )
    return get_task(connection, task_id)


def list_tasks(connection: Connection) -> list[TaskRead]:
    rows = connection.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    return [_row_to_task(row) for row in rows]


def get_task(connection: Connection, task_id: str) -> TaskRead | None:
    row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        return None
    return _row_to_task(row)


def update_task(connection: Connection, task_id: str, payload: TaskUpdate) -> TaskRead | None:
    existing = get_task(connection, task_id)
    if existing is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return existing

    update_data["updated_at"] = _now_iso()
    assignments = ", ".join(f"{field} = ?" for field in update_data)
    values = [
        value.value if isinstance(value, TaskStatus) else value
        for value in update_data.values()
    ]
    connection.execute(
        f"UPDATE tasks SET {assignments} WHERE id = ?",
        (*values, task_id),
    )
    return get_task(connection, task_id)


def delete_task(connection: Connection, task_id: str) -> bool:
    task_file_rows = connection.execute(
        """
        SELECT physical_file_id, COUNT(*) AS reference_count
        FROM task_files
        WHERE task_id = ?
        GROUP BY physical_file_id
        """,
        (task_id,),
    ).fetchall()

    cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    if cursor.rowcount == 0:
        return False

    now = _now_iso()
    for row in task_file_rows:
        connection.execute(
            """
            UPDATE physical_files
            SET ref_count = MAX(ref_count - ?, 0), updated_at = ?
            WHERE id = ?
            """,
            (row["reference_count"], now, row["physical_file_id"]),
        )
    return cursor.rowcount > 0
