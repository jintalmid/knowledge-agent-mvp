"""Legacy v0.2 retrieval and chunk compatibility service.

The v0.3 primary path uses Agent Runner plus Tool Registry. File selection is
handled by the runner prompt and tools such as list_file_summaries,
read_text_file, and analyze_excel_file.

This module remains available for the older retrieval page, chunk debug APIs,
and as migration input for the future M12 capability check. Embedding/hybrid
retrieval are still placeholders.
"""

import json
import re
from datetime import UTC, datetime
from sqlite3 import Connection, Row
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from app.schemas.retrieval import (
    ChunkMatchRead,
    DocumentChunkRead,
    RetrievalCandidateRead,
    RetrievalMode,
    RetrievalSettingsRead,
    RetrievalSettingsUpdate,
    RetrieveResponse,
)
from app.services.tasks import get_task

DEFAULT_RETRIEVAL_MODE: RetrievalMode = "summary_only"
DEFAULT_CHUNK_SIZE = 1600
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_TOP_K = 5
SUPPORTED_ACTIVE_MODES = {"summary_only", "chunk_text"}
RESERVED_MODES = {"embedding", "hybrid"}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _chunk_row_to_read(row: Row) -> DocumentChunkRead:
    data = dict(row)
    data["metadata_json"] = json.loads(data["metadata_json"])
    return DocumentChunkRead(**data)


def _settings_row_to_read(row: Row) -> RetrievalSettingsRead:
    return RetrievalSettingsRead(**dict(row))


def _default_settings() -> RetrievalSettingsRead:
    return RetrievalSettingsRead(
        retrieval_mode=DEFAULT_RETRIEVAL_MODE,
        chunk_size=DEFAULT_CHUNK_SIZE,
        chunk_overlap=DEFAULT_CHUNK_OVERLAP,
        top_k=DEFAULT_TOP_K,
        embedding_provider=None,
        embedding_model=None,
        vector_store=None,
        updated_at=datetime.now(UTC),
    )


def get_retrieval_settings(connection: Connection) -> RetrievalSettingsRead:
    row = connection.execute("SELECT * FROM retrieval_settings WHERE id = 'default'").fetchone()
    if row is not None:
        return _settings_row_to_read(row)

    settings = _default_settings()
    connection.execute(
        """
        INSERT INTO retrieval_settings (
            id,
            retrieval_mode,
            chunk_size,
            chunk_overlap,
            top_k,
            embedding_provider,
            embedding_model,
            vector_store,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "default",
            settings.retrieval_mode,
            settings.chunk_size,
            settings.chunk_overlap,
            settings.top_k,
            settings.embedding_provider,
            settings.embedding_model,
            settings.vector_store,
            settings.updated_at.isoformat(),
        ),
    )
    return settings


def update_retrieval_settings(connection: Connection, payload: RetrievalSettingsUpdate) -> RetrievalSettingsRead:
    current = get_retrieval_settings(connection)
    chunk_size = payload.chunk_size if payload.chunk_size is not None else current.chunk_size
    chunk_overlap = payload.chunk_overlap if payload.chunk_overlap is not None else current.chunk_overlap
    if chunk_overlap >= chunk_size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="chunk_overlap must be smaller than chunk_size")

    now = _now_iso()
    connection.execute(
        """
        UPDATE retrieval_settings
        SET retrieval_mode = ?,
            chunk_size = ?,
            chunk_overlap = ?,
            top_k = ?,
            embedding_provider = ?,
            embedding_model = ?,
            vector_store = ?,
            updated_at = ?
        WHERE id = 'default'
        """,
        (
            payload.retrieval_mode or current.retrieval_mode,
            chunk_size,
            chunk_overlap,
            payload.top_k or current.top_k,
            payload.embedding_provider if payload.embedding_provider is not None else current.embedding_provider,
            payload.embedding_model if payload.embedding_model is not None else current.embedding_model,
            payload.vector_store if payload.vector_store is not None else current.vector_store,
            now,
        ),
    )
    return get_retrieval_settings(connection)


def _get_chunk_source(connection: Connection, task_file_id: str) -> Row | None:
    return connection.execute(
        """
        SELECT
            tf.id AS task_file_id,
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


def _iter_text_chunks(text: str, chunk_size: int, chunk_overlap: int) -> list[tuple[str, dict[str, Any]]]:
    clean_text = text.strip()
    if not clean_text:
        return []

    chunks = []
    start = 0
    while start < len(clean_text):
        end = min(start + chunk_size, len(clean_text))
        content = clean_text[start:end].strip()
        if content:
            chunks.append((content, {"start_char": start, "end_char": end}))
        if end >= len(clean_text):
            break
        start = max(end - chunk_overlap, start + 1)
    return chunks


def _excel_sheet_to_chunk(display_name: str, profile: dict[str, Any], sheet: dict[str, Any]) -> str:
    columns = sheet.get("columns") if isinstance(sheet.get("columns"), list) else []
    column_text = ", ".join(
        f"{column.get('name', 'unknown')}({column.get('inferred_type', 'unknown')})"
        for column in columns
        if isinstance(column, dict)
    )
    sample_rows = sheet.get("sample_rows") if isinstance(sheet.get("sample_rows"), list) else []
    sample_preview = json.dumps(sample_rows[:3], ensure_ascii=False)
    return (
        f"File: {display_name}\n"
        f"Format: {profile.get('format', 'table')}\n"
        f"Sheet: {sheet.get('sheet_name', 'sheet')}\n"
        f"Rows: {sheet.get('row_count', 0)}, columns: {sheet.get('column_count', 0)}\n"
        f"Columns: {column_text}\n"
        f"Sample rows: {sample_preview}"
    )


def _build_excel_chunks(display_name: str, excel_profile_json: str | None) -> list[tuple[str, dict[str, Any]]]:
    profile = json.loads(excel_profile_json or "{}")
    sheets = profile.get("sheets") if isinstance(profile.get("sheets"), list) else []
    chunks = []
    for sheet_index, sheet in enumerate(sheets):
        if not isinstance(sheet, dict):
            continue
        chunks.append(
            (
                _excel_sheet_to_chunk(display_name, profile, sheet),
                {
                    "content_type": "excel",
                    "format": profile.get("format"),
                    "sheet_index": sheet_index,
                    "sheet_name": sheet.get("sheet_name"),
                },
            )
        )
    if chunks:
        return chunks
    return [(f"File: {display_name}\nExcel profile: {json.dumps(profile, ensure_ascii=False)[:3000]}", {"content_type": "excel"})]


def generate_task_file_chunks(connection: Connection, task_file_id: str) -> list[DocumentChunkRead]:
    source = _get_chunk_source(connection, task_file_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task file not found")
    if source["content_type"] is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="task file has not been parsed")

    settings = get_retrieval_settings(connection)
    if source["content_type"] == "text":
        raw_chunks = _iter_text_chunks(source["text_content"] or "", settings.chunk_size, settings.chunk_overlap)
        raw_chunks = [(content, {"content_type": "text", **metadata}) for content, metadata in raw_chunks]
    elif source["content_type"] == "excel":
        raw_chunks = _build_excel_chunks(source["display_name"], source["excel_profile_json"])
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported parsed content type")

    if not raw_chunks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="parsed content is empty")

    connection.execute("DELETE FROM document_chunks WHERE task_file_id = ?", (task_file_id,))
    now = _now_iso()
    for index, (content, metadata) in enumerate(raw_chunks):
        metadata_json = {
            "display_name": source["display_name"],
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            **metadata,
        }
        connection.execute(
            """
            INSERT INTO document_chunks (
                id,
                task_file_id,
                physical_file_id,
                chunk_index,
                content,
                metadata_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"chunk_{uuid4().hex}",
                task_file_id,
                source["physical_file_id"],
                index,
                content,
                json.dumps(metadata_json, ensure_ascii=False),
                now,
            ),
        )
    connection.execute(
        "UPDATE task_files SET embedding_status = ?, updated_at = ? WHERE id = ?",
        ("chunked", now, task_file_id),
    )
    return list_task_file_chunks(connection, task_file_id)


def list_task_file_chunks(connection: Connection, task_file_id: str) -> list[DocumentChunkRead]:
    rows = connection.execute(
        "SELECT * FROM document_chunks WHERE task_file_id = ? ORDER BY chunk_index ASC",
        (task_file_id,),
    ).fetchall()
    return [_chunk_row_to_read(row) for row in rows]


def _query_terms(question: str) -> list[str]:
    lowered = question.lower()
    ascii_terms = re.findall(r"[a-z0-9_]{2,}", lowered)
    cjk_terms = re.findall(r"[\u4e00-\u9fff]", lowered)
    terms = ascii_terms + cjk_terms
    seen = set()
    unique_terms = []
    for term in terms:
        if term not in seen:
            seen.add(term)
            unique_terms.append(term)
    return unique_terms or [lowered.strip()]


def _score_text(question: str, terms: list[str], value: str | None, weight: float) -> tuple[float, bool]:
    if not value:
        return 0.0, False
    text = value.lower()
    score = 0.0
    matched = False
    if question.lower().strip() and question.lower().strip() in text:
        score += weight * 2.0
        matched = True
    for term in terms:
        if term and term in text:
            score += weight
            matched = True
    return score, matched


def _preview(value: str, limit: int = 180) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def _unique(values: list[str]) -> list[str]:
    seen = set()
    unique_values = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique_values.append(value)
    return unique_values


def _retrieve_summary_only(connection: Connection, task_id: str, question: str, top_k: int) -> list[RetrievalCandidateRead]:
    terms = _query_terms(question)
    rows = connection.execute(
        """
        SELECT
            tf.id AS task_file_id,
            tf.physical_file_id,
            tf.display_name,
            fs.summary_text,
            fs.keywords_json,
            fs.tags_json,
            fs.category
        FROM task_files tf
        JOIN file_summaries fs ON fs.task_file_id = tf.id
        WHERE tf.task_id = ?
        """,
        (task_id,),
    ).fetchall()

    results = []
    for row in rows:
        score = 0.0
        matched_fields = []
        field_score, matched = _score_text(question, terms, row["display_name"], 1.5)
        score += field_score
        if matched:
            matched_fields.append("display_name")
        field_score, matched = _score_text(question, terms, row["summary_text"], 3.0)
        score += field_score
        if matched:
            matched_fields.append("summary_text")
        field_score, matched = _score_text(question, terms, row["category"], 2.0)
        score += field_score
        if matched:
            matched_fields.append("category")

        keywords = json.loads(row["keywords_json"] or "[]")
        tags = json.loads(row["tags_json"] or "[]")
        tag_text = " ".join(str(item) for item in [*keywords, *tags])
        field_score, matched = _score_text(question, terms, tag_text, 4.0)
        score += field_score
        if matched:
            matched_fields.append("keywords_tags")

        if score > 0:
            results.append(
                RetrievalCandidateRead(
                    task_file_id=row["task_file_id"],
                    physical_file_id=row["physical_file_id"],
                    display_name=row["display_name"],
                    score=round(score, 3),
                    matched_fields=_unique(matched_fields),
                    reason=f"命中摘要/标签字段：{', '.join(_unique(matched_fields))}",
                )
            )
    return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]


def _retrieve_chunk_text(connection: Connection, task_id: str, question: str, top_k: int) -> list[RetrievalCandidateRead]:
    terms = _query_terms(question)
    rows = connection.execute(
        """
        SELECT
            tf.id AS task_file_id,
            tf.physical_file_id,
            tf.display_name,
            dc.id AS chunk_id,
            dc.chunk_index,
            dc.content
        FROM task_files tf
        JOIN document_chunks dc ON dc.task_file_id = tf.id
        WHERE tf.task_id = ?
        ORDER BY tf.created_at ASC, dc.chunk_index ASC
        """,
        (task_id,),
    ).fetchall()

    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        chunk_score, chunk_matched = _score_text(question, terms, row["content"], 3.0)
        name_score, name_matched = _score_text(question, terms, row["display_name"], 1.0)
        score = chunk_score + name_score
        if score <= 0:
            continue

        item = grouped.setdefault(
            row["task_file_id"],
            {
                "task_file_id": row["task_file_id"],
                "physical_file_id": row["physical_file_id"],
                "display_name": row["display_name"],
                "score": 0.0,
                "matched_fields": [],
                "chunk_matches": [],
            },
        )
        item["score"] += score
        if chunk_matched:
            item["matched_fields"].append("chunk_content")
        if name_matched:
            item["matched_fields"].append("display_name")
        item["chunk_matches"].append(
            ChunkMatchRead(
                chunk_id=row["chunk_id"],
                chunk_index=row["chunk_index"],
                score=round(score, 3),
                preview=_preview(row["content"]),
            )
        )

    results = []
    for item in grouped.values():
        chunk_matches = sorted(item["chunk_matches"], key=lambda match: match.score, reverse=True)[:3]
        results.append(
            RetrievalCandidateRead(
                task_file_id=item["task_file_id"],
                physical_file_id=item["physical_file_id"],
                display_name=item["display_name"],
                score=round(item["score"], 3),
                matched_fields=_unique(item["matched_fields"]),
                reason=f"命中 {len(chunk_matches)} 个 chunk，最高分 {chunk_matches[0].score if chunk_matches else 0}",
                chunk_matches=chunk_matches,
            )
        )
    return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]


def retrieve_task_files(
    connection: Connection,
    task_id: str,
    question: str,
    retrieval_mode: RetrievalMode | None,
    top_k: int | None,
) -> RetrieveResponse:
    task = get_task(connection, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")

    settings = get_retrieval_settings(connection)
    mode = retrieval_mode or settings.retrieval_mode
    limit = top_k or settings.top_k

    if mode in RESERVED_MODES:
        return RetrieveResponse(
            retrieval_mode=mode,
            status="reserved",
            message=f"{mode} 已预留，阶段 0 未启用向量检索。",
            results=[],
        )

    if mode == "summary_only":
        results = _retrieve_summary_only(connection, task_id, question, limit)
        return RetrieveResponse(
            retrieval_mode=mode,
            status="ok",
            message="基于文件摘要、关键词、标签和分类进行轻量匹配。",
            results=results,
        )

    if mode == "chunk_text":
        results = _retrieve_chunk_text(connection, task_id, question, limit)
        return RetrieveResponse(
            retrieval_mode=mode,
            status="ok",
            message="基于已生成的 document_chunks 进行轻量文本匹配。",
            results=results,
        )

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported retrieval mode")
