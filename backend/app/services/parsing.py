import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from sqlite3 import Connection, Row
from typing import Any
from uuid import uuid4

import openpyxl
import xlrd
from fastapi import HTTPException, status
from pypdf import PdfReader

from app.schemas.parsing import ParsedContentRead
from app.services.tasks import get_task

TEXT_EXTENSIONS = {"txt", "md", "pdf"}
TABLE_EXTENSIONS = {"csv", "xlsx", "xls"}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _row_to_parsed_content(row: Row) -> ParsedContentRead:
    data = dict(row)
    if data["excel_profile_json"]:
        data["excel_profile_json"] = json.loads(data["excel_profile_json"])
    else:
        data["excel_profile_json"] = None
    return ParsedContentRead(**data)


def _get_task_file_parse_source(connection: Connection, task_file_id: str) -> Row | None:
    return connection.execute(
        """
        SELECT
            tf.id AS task_file_id,
            tf.task_id,
            tf.physical_file_id,
            tf.display_name,
            pf.file_ext,
            pf.storage_path
        FROM task_files tf
        JOIN physical_files pf ON pf.id = tf.physical_file_id
        WHERE tf.id = ?
        """,
        (task_file_id,),
    ).fetchone()


def _preview_error(value: str, limit: int = 500) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[:limit]}..."


def _error_detail(exc: HTTPException | Exception) -> str:
    if isinstance(exc, HTTPException):
        return _preview_error(str(exc.detail))
    return _preview_error(str(exc))


def set_parse_status(
    connection: Connection,
    task_file_id: str,
    parse_status: str,
    parse_error: str | None = None,
) -> None:
    connection.execute(
        "UPDATE task_files SET parse_status = ?, parse_error = ?, updated_at = ? WHERE id = ?",
        (parse_status, parse_error, _now_iso(), task_file_id),
    )


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _read_pdf_text(path: Path) -> str:
    reader = PdfReader(path)
    page_text = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            page_text.append(f"--- page {index} ---\n{text.strip()}")
    return "\n\n".join(page_text)


def _infer_value_type(value: Any) -> str:
    if value is None or value == "":
        return "empty"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, datetime):
        return "datetime"
    text = str(value).strip()
    if not text:
        return "empty"
    try:
        int(text)
        return "integer"
    except ValueError:
        pass
    try:
        float(text)
        return "number"
    except ValueError:
        pass
    return "text"


def _merge_types(types: list[str]) -> str:
    meaningful = [item for item in types if item != "empty"]
    if not meaningful:
        return "empty"
    unique = set(meaningful)
    if len(unique) == 1:
        return meaningful[0]
    if unique <= {"integer", "number"}:
        return "number"
    return "mixed"


def _normalize_cell(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _build_sheet_profile(sheet_name: str, rows: list[list[Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "sheet_name": sheet_name,
            "row_count": 0,
            "column_count": 0,
            "columns": [],
            "sample_rows": [],
        }

    header = [str(cell).strip() if cell not in (None, "") else f"column_{index + 1}" for index, cell in enumerate(rows[0])]
    data_rows = rows[1:]
    column_count = len(header)
    normalized_rows = [row + [None] * (column_count - len(row)) for row in data_rows]

    columns = []
    for index, column_name in enumerate(header):
        values = [row[index] if index < len(row) else None for row in normalized_rows[:100]]
        columns.append(
            {
                "name": column_name,
                "inferred_type": _merge_types([_infer_value_type(value) for value in values]),
            }
        )

    sample_rows = []
    for row in normalized_rows[:10]:
        sample_rows.append(
            {
                header[index]: _normalize_cell(row[index] if index < len(row) else None)
                for index in range(column_count)
            }
        )

    return {
        "sheet_name": sheet_name,
        "row_count": len(data_rows),
        "column_count": column_count,
        "columns": columns,
        "sample_rows": sample_rows,
    }


def _parse_csv(path: Path) -> dict[str, Any]:
    text = _read_text(path)
    rows = list(csv.reader(text.splitlines()))
    sheet_profile = _build_sheet_profile("csv", rows)
    return {
        "format": "csv",
        "sheet_count": 1,
        "sheets": [sheet_profile],
    }


def _parse_xlsx(path: Path) -> dict[str, Any]:
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheets = []
    try:
        for worksheet in workbook.worksheets:
            rows = [list(row) for row in worksheet.iter_rows(values_only=True)]
            sheets.append(_build_sheet_profile(worksheet.title, rows))
    finally:
        workbook.close()
    return {
        "format": "xlsx",
        "sheet_count": len(sheets),
        "sheets": sheets,
    }


def _parse_xls(path: Path) -> dict[str, Any]:
    workbook = xlrd.open_workbook(path)
    sheets = []
    for sheet in workbook.sheets():
        rows = [sheet.row_values(index) for index in range(sheet.nrows)]
        sheets.append(_build_sheet_profile(sheet.name, rows))
    return {
        "format": "xls",
        "sheet_count": len(sheets),
        "sheets": sheets,
    }


def _save_parsed_content(
    connection: Connection,
    task_file_id: str,
    physical_file_id: str,
    content_type: str,
    text_content: str | None,
    excel_profile: dict[str, Any] | None,
    parse_quality: str,
) -> ParsedContentRead:
    parsed_content_id = f"pc_{uuid4().hex}"
    now = _now_iso()
    excel_profile_json = json.dumps(excel_profile, ensure_ascii=False) if excel_profile is not None else None
    connection.execute(
        """
        INSERT INTO parsed_contents (
            id,
            task_file_id,
            physical_file_id,
            content_type,
            text_content,
            excel_profile_json,
            parse_quality,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(task_file_id) DO UPDATE SET
            physical_file_id = excluded.physical_file_id,
            content_type = excluded.content_type,
            text_content = excluded.text_content,
            excel_profile_json = excluded.excel_profile_json,
            parse_quality = excluded.parse_quality,
            updated_at = excluded.updated_at
        """,
        (
            parsed_content_id,
            task_file_id,
            physical_file_id,
            content_type,
            text_content,
            excel_profile_json,
            parse_quality,
            now,
            now,
        ),
    )
    parsed_content = get_parsed_content(connection, task_file_id)
    if parsed_content is None:
        raise HTTPException(status_code=500, detail="failed to save parsed content")
    return parsed_content


def parse_task_file(connection: Connection, task_file_id: str) -> ParsedContentRead:
    source = _get_task_file_parse_source(connection, task_file_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task file not found")

    path = Path(source["storage_path"])
    file_ext = source["file_ext"].lower()
    if not path.exists():
        set_parse_status(connection, task_file_id, "failed", "stored file not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="stored file not found")

    set_parse_status(connection, task_file_id, "parsing", None)
    try:
        if file_ext in {"txt", "md"}:
            parsed_content = _save_parsed_content(
                connection=connection,
                task_file_id=task_file_id,
                physical_file_id=source["physical_file_id"],
                content_type="text",
                text_content=_read_text(path),
                excel_profile=None,
                parse_quality="ok",
            )
        elif file_ext == "pdf":
            parsed_content = _save_parsed_content(
                connection=connection,
                task_file_id=task_file_id,
                physical_file_id=source["physical_file_id"],
                content_type="text",
                text_content=_read_pdf_text(path),
                excel_profile=None,
                parse_quality="ok",
            )
        elif file_ext == "csv":
            parsed_content = _save_parsed_content(
                connection=connection,
                task_file_id=task_file_id,
                physical_file_id=source["physical_file_id"],
                content_type="excel",
                text_content=None,
                excel_profile=_parse_csv(path),
                parse_quality="ok",
            )
        elif file_ext == "xlsx":
            parsed_content = _save_parsed_content(
                connection=connection,
                task_file_id=task_file_id,
                physical_file_id=source["physical_file_id"],
                content_type="excel",
                text_content=None,
                excel_profile=_parse_xlsx(path),
                parse_quality="ok",
            )
        elif file_ext == "xls":
            parsed_content = _save_parsed_content(
                connection=connection,
                task_file_id=task_file_id,
                physical_file_id=source["physical_file_id"],
                content_type="excel",
                text_content=None,
                excel_profile=_parse_xls(path),
                parse_quality="ok",
            )
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported file type")
    except HTTPException as exc:
        set_parse_status(connection, task_file_id, "failed", _error_detail(exc))
        raise
    except Exception as exc:
        set_parse_status(connection, task_file_id, "failed", f"parse failed: {_error_detail(exc)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"parse failed: {exc}") from exc

    set_parse_status(connection, task_file_id, "parsed", None)
    return parsed_content


def parse_all_task_files(connection: Connection, task_id: str) -> list[ParsedContentRead]:
    task = get_task(connection, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")

    rows = connection.execute(
        "SELECT id FROM task_files WHERE task_id = ? ORDER BY created_at ASC",
        (task_id,),
    ).fetchall()
    parsed_contents = []
    for row in rows:
        parsed_contents.append(parse_task_file(connection, row["id"]))
    return parsed_contents


def get_parsed_content(connection: Connection, task_file_id: str) -> ParsedContentRead | None:
    row = connection.execute(
        "SELECT * FROM parsed_contents WHERE task_file_id = ?",
        (task_file_id,),
    ).fetchone()
    if row is None:
        return None
    return _row_to_parsed_content(row)
