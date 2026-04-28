"""Legacy v0.2 text QA compatibility service.

The v0.3 primary path is Agent Runner:
POST /api/tasks/{task_id}/agent-runs -> tool calls -> observations -> final answer.

This module remains available for the older /ask page and for reading historical
answers via /results. Do not add new Agent Runner behavior here.
"""

import json
from datetime import UTC, datetime
from sqlite3 import Connection, Row
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from app.schemas.qa import AnswerRead, SourceRefRead
from app.services import llm as llm_service
from app.services import retrieval as retrieval_service
from app.services.tasks import get_task

MAX_CONTEXT_FILES = 5
MAX_CONTEXT_CHUNKS_PER_FILE = 4
MAX_TEXT_CONTEXT_CHARS = 6500


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _preview(value: str, limit: int = 500) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def _json_loads(value: str) -> Any:
    return json.loads(value) if value else None


def _answer_row_to_read(row: Row) -> AnswerRead:
    data = dict(row)
    data["selected_task_file_ids_json"] = _json_loads(data["selected_task_file_ids_json"]) or []
    data["source_refs_json"] = _json_loads(data["source_refs_json"]) or []
    return AnswerRead(**data)


def _insert_question(connection: Connection, task_id: str, question_text: str) -> str:
    question_id = f"q_{uuid4().hex}"
    connection.execute(
        """
        INSERT INTO questions (
            id,
            task_id,
            question_text,
            question_type,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (question_id, task_id, question_text, "text_qa", _now_iso()),
    )
    return question_id


def _get_text_source(connection: Connection, task_file_id: str) -> Row | None:
    return connection.execute(
        """
        SELECT
            tf.id AS task_file_id,
            tf.physical_file_id,
            tf.display_name,
            pc.content_type,
            pc.text_content
        FROM task_files tf
        JOIN parsed_contents pc ON pc.task_file_id = tf.id
        WHERE tf.id = ? AND pc.content_type = 'text'
        """,
        (task_file_id,),
    ).fetchone()


def _get_chunks_by_ids(connection: Connection, task_file_id: str, chunk_ids: list[str]) -> list[Row]:
    if not chunk_ids:
        return []
    placeholders = ",".join("?" for _ in chunk_ids)
    rows = connection.execute(
        f"""
        SELECT *
        FROM document_chunks
        WHERE task_file_id = ? AND id IN ({placeholders})
        ORDER BY chunk_index ASC
        """,
        (task_file_id, *chunk_ids),
    ).fetchall()
    by_id = {row["id"]: row for row in rows}
    return [by_id[chunk_id] for chunk_id in chunk_ids if chunk_id in by_id]


def _get_top_chunks(connection: Connection, task_file_id: str, limit: int) -> list[Row]:
    return connection.execute(
        """
        SELECT *
        FROM document_chunks
        WHERE task_file_id = ?
        ORDER BY chunk_index ASC
        LIMIT ?
        """,
        (task_file_id, limit),
    ).fetchall()


def _context_from_text(text: str) -> tuple[str, list[dict[str, Any]]]:
    content = text[:MAX_TEXT_CONTEXT_CHARS]
    return content, [{"type": "parsed_text", "preview": _preview(content)}]


def _context_from_chunks(chunks: list[Row]) -> tuple[str, list[dict[str, Any]]]:
    parts = []
    refs = []
    for row in chunks[:MAX_CONTEXT_CHUNKS_PER_FILE]:
        content = str(row["content"])
        parts.append(f"[chunk {row['chunk_index']}]\n{content}")
        refs.append(
            {
                "type": "chunk",
                "chunk_id": row["id"],
                "chunk_index": row["chunk_index"],
                "preview": _preview(content),
            }
        )
    return "\n\n".join(parts)[:MAX_TEXT_CONTEXT_CHARS], refs


def _build_context(connection: Connection, candidates: list[Any]) -> tuple[list[str], list[dict[str, Any]], str]:
    selected_task_file_ids = []
    source_refs = []
    prompt_sections = []

    for candidate in candidates[:MAX_CONTEXT_FILES]:
        source = _get_text_source(connection, candidate.task_file_id)
        if source is None:
            continue

        chunk_ids = [match.chunk_id for match in candidate.chunk_matches]
        chunks = _get_chunks_by_ids(connection, candidate.task_file_id, chunk_ids)
        if not chunks:
            chunks = _get_top_chunks(connection, candidate.task_file_id, MAX_CONTEXT_CHUNKS_PER_FILE)

        if chunks:
            context_content, chunk_refs = _context_from_chunks(chunks)
        else:
            context_content, chunk_refs = _context_from_text(source["text_content"] or "")

        if not context_content.strip():
            continue

        selected_task_file_ids.append(source["task_file_id"])
        source_refs.append(
            {
                "task_file_id": source["task_file_id"],
                "physical_file_id": source["physical_file_id"],
                "display_name": source["display_name"],
                "score": candidate.score,
                "matched_fields": candidate.matched_fields,
                "reason": candidate.reason,
                "content_type": source["content_type"],
                "chunk_refs": chunk_refs,
            }
        )
        prompt_sections.append(
            "\n".join(
                [
                    f"Source file: {source['display_name']}",
                    f"task_file_id: {source['task_file_id']}",
                    f"retrieval_score: {candidate.score}",
                    "Content:",
                    context_content,
                ]
            )
        )

    return selected_task_file_ids, source_refs, "\n\n---\n\n".join(prompt_sections)


def _build_prompt(question_text: str, context_text: str, source_refs: list[dict[str, Any]]) -> tuple[str, str]:
    source_names = [source["display_name"] for source in source_refs]
    system_prompt = (
        "You are an enterprise knowledge assistant. Answer only from the provided source context. "
        "Do not invent facts that are not supported by the context. If the context is insufficient, say what is uncertain. "
        "Output Markdown only."
    )
    user_prompt = (
        "Answer the user's question directly in Markdown.\n"
        "Requirements:\n"
        "- Use only the provided source context.\n"
        "- State which files support the answer.\n"
        "- Clearly mention uncertainty or missing information.\n"
        "- Do not fabricate information.\n\n"
        f"User question:\n{question_text}\n\n"
        f"Selected source files:\n{json.dumps(source_names, ensure_ascii=False)}\n\n"
        f"Source context:\n{context_text}"
    )
    return system_prompt, user_prompt


def ask_task_question(connection: Connection, task_id: str, question_text: str) -> AnswerRead:
    task = get_task(connection, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")

    normalized_question = question_text.strip()
    question_id = _insert_question(connection, task_id, normalized_question)
    retrieval_response = retrieval_service.retrieve_task_files(
        connection,
        task_id=task_id,
        question=normalized_question,
        retrieval_mode=None,
        top_k=None,
    )
    if retrieval_response.status != "ok":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=retrieval_response.message)

    selected_task_file_ids, source_refs, context_text = _build_context(connection, retrieval_response.results)
    if not selected_task_file_ids or not context_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="no parsed text sources matched the question; parse/summarize text files or switch retrieval settings",
        )

    system_prompt, user_prompt = _build_prompt(normalized_question, context_text, source_refs)
    llm_result = llm_service.call_llm(
        connection,
        task_id=task_id,
        scenario="final_answer",
        module_name="M09_TEXT_QA_PROCESSING",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    answer_id = f"ans_{uuid4().hex}"
    now = _now_iso()
    connection.execute(
        """
        INSERT INTO answers (
            id,
            task_id,
            question_id,
            answer_text_markdown,
            selected_task_file_ids_json,
            source_refs_json,
            iteration_count,
            llm_provider,
            llm_model,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            answer_id,
            task_id,
            question_id,
            llm_result.text,
            json.dumps(selected_task_file_ids, ensure_ascii=False),
            json.dumps(source_refs, ensure_ascii=False),
            task.iteration_count,
            llm_result.provider_type,
            llm_result.model_name,
            now,
        ),
    )
    answer = get_answer(connection, answer_id)
    if answer is None:
        raise HTTPException(status_code=500, detail="failed to save answer")
    return answer


def list_task_results(connection: Connection, task_id: str) -> list[AnswerRead] | None:
    task = get_task(connection, task_id)
    if task is None:
        return None
    rows = connection.execute(
        """
        SELECT
            a.*,
            q.question_text,
            q.question_type
        FROM answers a
        JOIN questions q ON q.id = a.question_id
        WHERE a.task_id = ?
        ORDER BY a.created_at DESC
        """,
        (task_id,),
    ).fetchall()
    return [_answer_row_to_read(row) for row in rows]


def get_answer(connection: Connection, answer_id: str) -> AnswerRead | None:
    row = connection.execute(
        """
        SELECT
            a.*,
            q.question_text,
            q.question_type
        FROM answers a
        JOIN questions q ON q.id = a.question_id
        WHERE a.id = ?
        """,
        (answer_id,),
    ).fetchone()
    if row is None:
        return None
    return _answer_row_to_read(row)
