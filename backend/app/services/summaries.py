import json
from datetime import UTC, datetime
from sqlite3 import Connection, Row
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from app.schemas.summary import FileSummaryRead
from app.services import llm as llm_service
from app.services.parsing import get_parsed_content
from app.services.tasks import get_task


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _extract_json_object(value: str) -> dict[str, Any]:
    text = value.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("LLM response does not contain a JSON object")
    return json.loads(text[start : end + 1])


def _ensure_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _summary_row_to_read(row: Row) -> FileSummaryRead:
    data = dict(row)
    data["keywords_json"] = json.loads(data["keywords_json"])
    data["tags_json"] = json.loads(data["tags_json"])
    if data.get("table_understanding_json"):
        data["table_understanding"] = json.loads(data["table_understanding_json"])
    else:
        data["table_understanding"] = None
    data.pop("table_understanding_json", None)
    return FileSummaryRead(**data)


def _get_summary_source(connection: Connection, task_file_id: str) -> Row | None:
    return connection.execute(
        """
        SELECT
            tf.id AS task_file_id,
            tf.task_id,
            tf.physical_file_id,
            tf.display_name,
            pc.content_type,
            pc.text_content,
            pc.excel_profile_json
        FROM task_files tf
        LEFT JOIN parsed_contents pc ON pc.task_file_id = tf.id
        WHERE tf.id = ?
        """,
        (task_file_id,),
    ).fetchone()


def _set_summary_status(connection: Connection, task_file_id: str, summary_status: str) -> None:
    connection.execute(
        "UPDATE task_files SET summary_status = ?, updated_at = ? WHERE id = ?",
        (summary_status, _now_iso(), task_file_id),
    )


def _build_prompt(source: Row) -> tuple[str, str]:
    system_prompt = (
        "You are a concise enterprise knowledge assistant. "
        "Write every human-readable JSON value in the same primary language as the source file. "
        "For mixed-language files, use the dominant language in the content, column names, and samples. "
        "Return only valid JSON. Do not include markdown fences or extra commentary."
    )
    if source["content_type"] == "text":
        text = (source["text_content"] or "")[:16000]
        user_prompt = (
            "Summarize this text file. Return exactly this JSON schema:\n"
            '{"summary":"...","keywords":[],"tags":[],"category":"..."}\n\n'
            "Language rule: detect the source file's primary language from the content and use that same language "
            "for summary, keywords, tags, and category. Do not translate into another language.\n"
            f"File name: {source['display_name']}\n"
            f"Content:\n{text}"
        )
    elif source["content_type"] == "excel":
        profile = source["excel_profile_json"] or "{}"
        user_prompt = (
            "Summarize this table profile. Return exactly this JSON schema:\n"
            '{"summary":"...","keywords":[],"tags":[],"category":"...",'
            '"table_understanding":{"main_subject":"...","important_columns":[],"possible_questions":[]}}\n\n'
            "Language rule: infer the source file's primary language from the file name, sheet names, column names, "
            "and sample rows. Use that same language for summary, keywords, tags, category, and table_understanding. "
            "Do not translate into another language.\n"
            f"File name: {source['display_name']}\n"
            f"Excel profile JSON:\n{profile[:18000]}"
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported parsed content type")
    return system_prompt, user_prompt


def summarize_task_file(connection: Connection, task_file_id: str) -> FileSummaryRead:
    source = _get_summary_source(connection, task_file_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task file not found")
    parsed_content = get_parsed_content(connection, task_file_id)
    if parsed_content is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="task file has not been parsed")

    _set_summary_status(connection, task_file_id, "summarizing")
    try:
        system_prompt, user_prompt = _build_prompt(source)
        llm_result = llm_service.call_llm(
            connection,
            task_id=source["task_id"],
            module_name="M06_LLM_SUMMARY_TAGGING",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        parsed_response = _extract_json_object(llm_result.text)
        summary_text = str(parsed_response.get("summary") or "").strip()
        if not summary_text:
            raise ValueError("LLM JSON missing summary")
        keywords = _ensure_string_list(parsed_response.get("keywords"))
        tags = _ensure_string_list(parsed_response.get("tags"))
        category = str(parsed_response.get("category") or "uncategorized")
        table_understanding = parsed_response.get("table_understanding")
        if not isinstance(table_understanding, dict):
            table_understanding = None
    except HTTPException:
        _set_summary_status(connection, task_file_id, "failed")
        connection.commit()
        raise
    except Exception as exc:
        _set_summary_status(connection, task_file_id, "failed")
        connection.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"summary failed: {exc}") from exc

    summary_id = f"sum_{uuid4().hex}"
    now = _now_iso()
    connection.execute(
        """
        INSERT INTO file_summaries (
            id,
            task_file_id,
            physical_file_id,
            summary_text,
            keywords_json,
            tags_json,
            category,
            summary_method,
            llm_provider,
            llm_model,
            knowledge_item_id,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(task_file_id) DO UPDATE SET
            physical_file_id = excluded.physical_file_id,
            summary_text = excluded.summary_text,
            keywords_json = excluded.keywords_json,
            tags_json = excluded.tags_json,
            category = excluded.category,
            summary_method = excluded.summary_method,
            llm_provider = excluded.llm_provider,
            llm_model = excluded.llm_model,
            updated_at = excluded.updated_at
        """,
        (
            summary_id,
            task_file_id,
            source["physical_file_id"],
            summary_text,
            json.dumps(keywords, ensure_ascii=False),
            json.dumps(tags, ensure_ascii=False),
            category,
            "llm",
            llm_result.provider_type,
            llm_result.model_name,
            None,
            now,
            now,
        ),
    )
    if table_understanding is not None:
        saved_summary = get_task_file_summary(connection, task_file_id)
        if saved_summary is not None:
            connection.execute(
                """
                INSERT INTO file_summary_extras (file_summary_id, table_understanding_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(file_summary_id) DO UPDATE SET
                    table_understanding_json = excluded.table_understanding_json,
                    updated_at = excluded.updated_at
                """,
                (saved_summary.id, json.dumps(table_understanding, ensure_ascii=False), now),
            )
    else:
        saved_summary = get_task_file_summary(connection, task_file_id)
        if saved_summary is not None:
            connection.execute("DELETE FROM file_summary_extras WHERE file_summary_id = ?", (saved_summary.id,))

    _set_summary_status(connection, task_file_id, "summarized")
    summary = get_task_file_summary(connection, task_file_id)
    if summary is None:
        raise HTTPException(status_code=500, detail="failed to save summary")
    return summary


def summarize_all_task_files(connection: Connection, task_id: str) -> list[FileSummaryRead]:
    task = get_task(connection, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    rows = connection.execute(
        "SELECT id FROM task_files WHERE task_id = ? ORDER BY created_at ASC",
        (task_id,),
    ).fetchall()
    return [summarize_task_file(connection, row["id"]) for row in rows]


def list_task_summaries(connection: Connection, task_id: str) -> list[FileSummaryRead] | None:
    task = get_task(connection, task_id)
    if task is None:
        return None
    rows = connection.execute(
        """
        SELECT fs.*, fse.table_understanding_json
        FROM file_summaries fs
        JOIN task_files tf ON tf.id = fs.task_file_id
        LEFT JOIN file_summary_extras fse ON fse.file_summary_id = fs.id
        WHERE tf.task_id = ?
        ORDER BY fs.updated_at DESC
        """,
        (task_id,),
    ).fetchall()
    return [_summary_row_to_read(row) for row in rows]


def get_task_file_summary(connection: Connection, task_file_id: str) -> FileSummaryRead | None:
    row = connection.execute(
        """
        SELECT fs.*, fse.table_understanding_json
        FROM file_summaries fs
        LEFT JOIN file_summary_extras fse ON fse.file_summary_id = fs.id
        WHERE fs.task_file_id = ?
        """,
        (task_file_id,),
    ).fetchone()
    if row is None:
        return None
    return _summary_row_to_read(row)
