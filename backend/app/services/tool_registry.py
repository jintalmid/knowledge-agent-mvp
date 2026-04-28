import json
from sqlite3 import Connection, Row
from typing import Any

from fastapi import HTTPException, status

from app.schemas.tools import ToolCallResponse, ToolRead
from app.services import excel_analysis as excel_analysis_service
from app.services import llm as llm_service
from app.services.tasks import get_task

TEXT_CONTEXT_LIMIT = 18000


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


def _tool_definitions() -> dict[str, ToolRead]:
    return {
        "list_file_summaries": ToolRead(
            name="list_file_summaries",
            description="List summarized files in a task workspace so an Agent can choose relevant files.",
            input_schema={
                "type": "object",
                "required": ["task_id"],
                "properties": {
                    "task_id": {"type": "string"},
                },
            },
            output_schema={
                "type": "object",
                "properties": {
                    "summaries": {"type": "array"},
                },
            },
            safety_notes=["Read-only. Returns summary metadata only."],
        ),
        "read_text_file": ToolRead(
            name="read_text_file",
            description="Read one parsed text task file and ask the LLM to extract observation and evidence for a question.",
            input_schema={
                "type": "object",
                "required": ["task_id", "file_id", "question", "instruction"],
                "properties": {
                    "task_id": {"type": "string"},
                    "file_id": {"type": "string", "description": "task_file_id from task_files"},
                    "question": {"type": "string"},
                    "instruction": {"type": "string"},
                    "agent_run_id": {"type": "string"},
                    "iteration_id": {"type": "string"},
                },
            },
            output_schema={
                "type": "object",
                "properties": {
                    "observation": {"type": "string"},
                    "evidence": {"type": "array"},
                    "file": {"type": "object"},
                    "llm_log_id": {"type": "string"},
                },
            },
            safety_notes=[
                "Read-only.",
                "Only reads parsed_contents for task_files inside the provided task_id.",
                "Does not read arbitrary local paths.",
            ],
        ),
        "analyze_excel_file": ToolRead(
            name="analyze_excel_file",
            description="Analyze one parsed Excel-compatible task file by reusing the existing LLM Python generation and restricted sandbox execution.",
            input_schema={
                "type": "object",
                "required": ["task_id", "file_id", "question", "instruction"],
                "properties": {
                    "task_id": {"type": "string"},
                    "file_id": {"type": "string", "description": "task_file_id from task_files"},
                    "question": {"type": "string"},
                    "instruction": {"type": "string"},
                    "sheet_name": {"type": "string"},
                    "agent_run_id": {"type": "string"},
                    "iteration_id": {"type": "string"},
                },
            },
            output_schema={
                "type": "object",
                "properties": {
                    "observation": {"type": "string"},
                    "result_json": {"type": ["object", "array", "null"]},
                    "generated_code": {"type": "string"},
                    "execution_status": {"type": "string"},
                },
            },
            safety_notes=[
                "Reuses the existing Excel static safety checker and restricted subprocess execution.",
                "Only analyzes task_files that belong to the provided task_id.",
                "Execution writes result.json in a temporary directory and times out after 10 seconds.",
            ],
        ),
    }


def list_tools() -> list[ToolRead]:
    return list(_tool_definitions().values())


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{key} is required")
    return value.strip()


def _get_text_file_source(connection: Connection, task_id: str, file_id: str) -> Row | None:
    return connection.execute(
        """
        SELECT
            tf.id AS task_file_id,
            tf.task_id,
            tf.physical_file_id,
            tf.display_name,
            pc.content_type,
            pc.text_content,
            pc.parse_quality
        FROM task_files tf
        JOIN parsed_contents pc ON pc.task_file_id = tf.id
        WHERE tf.task_id = ? AND tf.id = ? AND pc.content_type = 'text'
        """,
        (task_id, file_id),
    ).fetchone()


def _call_list_file_summaries(connection: Connection, payload: dict[str, Any]) -> ToolCallResponse:
    task_id = _require_string(payload, "task_id")
    if get_task(connection, task_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")

    rows = connection.execute(
        """
        SELECT
            tf.id AS task_file_id,
            tf.display_name,
            fs.physical_file_id,
            fs.summary_text,
            fs.keywords_json,
            fs.tags_json,
            fs.category,
            fs.updated_at
        FROM file_summaries fs
        JOIN task_files tf ON tf.id = fs.task_file_id
        WHERE tf.task_id = ?
        ORDER BY fs.updated_at DESC
        """,
        (task_id,),
    ).fetchall()
    summaries = []
    for row in rows:
        summaries.append(
            {
                "task_file_id": row["task_file_id"],
                "file_id": row["task_file_id"],
                "physical_file_id": row["physical_file_id"],
                "display_name": row["display_name"],
                "summary": row["summary_text"],
                "keywords": json.loads(row["keywords_json"] or "[]"),
                "tags": json.loads(row["tags_json"] or "[]"),
                "category": row["category"],
                "updated_at": row["updated_at"],
            }
        )
    return ToolCallResponse(
        tool_name="list_file_summaries",
        status="success",
        output={"task_id": task_id, "summaries": summaries},
    )


def _build_read_text_prompt(source: Row, question: str, instruction: str) -> tuple[str, str]:
    content = (source["text_content"] or "")[:TEXT_CONTEXT_LIMIT]
    system_prompt = (
        "You are a careful file-reading tool for an Agent. "
        "Extract only information supported by the provided parsed file content. "
        "Return only valid JSON. Do not include markdown fences or commentary."
    )
    user_prompt = (
        "Read the parsed text file and return an observation for the Agent.\n"
        "Requirements:\n"
        "- Answer in the same primary language as the user question unless the instruction says otherwise.\n"
        "- Do not invent facts that are not in the file content.\n"
        "- If the file does not contain enough information, say so in observation.\n"
        "- Evidence must be short direct snippets or precise paraphrases grounded in the file.\n\n"
        "Return exactly this JSON schema:\n"
        '{"observation":"...","evidence":["..."],"confidence":"high|medium|low"}\n\n'
        f"File name: {source['display_name']}\n"
        f"task_file_id: {source['task_file_id']}\n"
        f"Question:\n{question}\n\n"
        f"Instruction:\n{instruction}\n\n"
        f"Parsed file content:\n{content}"
    )
    return system_prompt, user_prompt


def _call_read_text_file(connection: Connection, payload: dict[str, Any]) -> ToolCallResponse:
    task_id = _require_string(payload, "task_id")
    file_id = _require_string(payload, "file_id")
    question = _require_string(payload, "question")
    instruction = _require_string(payload, "instruction")
    agent_run_id = _optional_string(payload, "agent_run_id")
    iteration_id = _optional_string(payload, "iteration_id")

    if get_task(connection, task_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    source = _get_text_file_source(connection, task_id, file_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="parsed text file not found for this task_id and file_id",
        )

    system_prompt, user_prompt = _build_read_text_prompt(source, question, instruction)
    llm_result = llm_service.call_llm(
        connection,
        task_id=task_id,
        agent_run_id=agent_run_id,
        iteration_id=iteration_id,
        scenario="text_tool",
        module_name="M09_V03_TOOL_READ_TEXT_FILE",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    try:
        parsed = _extract_json_object(llm_result.text)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"read_text_file failed to parse LLM JSON: {exc}") from exc

    observation = str(parsed.get("observation") or "").strip()
    if not observation:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="read_text_file LLM JSON missing observation")
    evidence = _ensure_string_list(parsed.get("evidence"))
    confidence = str(parsed.get("confidence") or "medium")

    return ToolCallResponse(
        tool_name="read_text_file",
        status="success",
        output={
            "task_id": task_id,
            "file_id": file_id,
            "file": {
                "task_file_id": source["task_file_id"],
                "physical_file_id": source["physical_file_id"],
                "display_name": source["display_name"],
                "parse_quality": source["parse_quality"],
            },
            "observation": observation,
            "evidence": evidence,
            "confidence": confidence,
            "llm_log_id": llm_result.log_id,
        },
    )


def _optional_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{key} must be a string")
    clean_value = value.strip()
    return clean_value or None


def _get_task_file_for_tool(connection: Connection, task_id: str, file_id: str) -> Row | None:
    return connection.execute(
        """
        SELECT
            tf.id AS task_file_id,
            tf.task_id,
            tf.display_name,
            pf.file_ext,
            pc.content_type,
            pc.excel_profile_json
        FROM task_files tf
        JOIN physical_files pf ON pf.id = tf.physical_file_id
        LEFT JOIN parsed_contents pc ON pc.task_file_id = tf.id
        WHERE tf.task_id = ? AND tf.id = ?
        """,
        (task_id, file_id),
    ).fetchone()


def _call_analyze_excel_file(connection: Connection, payload: dict[str, Any]) -> ToolCallResponse:
    task_id = _require_string(payload, "task_id")
    file_id = _require_string(payload, "file_id")
    question = _require_string(payload, "question")
    instruction = _require_string(payload, "instruction")
    sheet_name = _optional_string(payload, "sheet_name")
    agent_run_id = _optional_string(payload, "agent_run_id")
    iteration_id = _optional_string(payload, "iteration_id")

    if get_task(connection, task_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    task_file = _get_task_file_for_tool(connection, task_id, file_id)
    if task_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task file not found for this task")
    if task_file["content_type"] != "excel" or not task_file["excel_profile_json"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="task file has not been parsed as Excel")

    combined_question = f"{question}\n\nInstruction for the analysis tool:\n{instruction}"
    response = excel_analysis_service.analyze_excel_task_file(
        connection,
        task_file_id=file_id,
        question=combined_question,
        sheet_name=sheet_name,
        agent_run_id=agent_run_id,
        iteration_id=iteration_id,
    )
    result_json = response.run.result_json
    if response.run.execution_status == "success":
        observation = f"Excel analysis succeeded for {task_file['display_name']}."
    else:
        observation = f"Excel analysis failed for {task_file['display_name']}: {response.run.first_error or response.run.stderr or 'unknown error'}"

    return ToolCallResponse(
        tool_name="analyze_excel_file",
        status="success" if response.run.execution_status == "success" else "failed",
        output={
            "task_id": task_id,
            "file_id": file_id,
            "run_id": response.run.id,
            "agent_run_id": response.run.agent_run_id,
            "iteration_id": response.run.iteration_id,
            "observation": observation,
            "result_json": result_json,
            "generated_code": response.run.generated_code,
            "final_code": response.run.final_code,
            "execution_status": response.run.execution_status,
            "code_status": response.run.code_status,
            "repair_attempts": response.run.repair_attempts,
            "stdout": response.run.stdout,
            "stderr": response.run.stderr,
            "first_error": None if response.run.execution_status == "success" else response.run.first_error,
        },
    )


def call_tool(connection: Connection, tool_name: str, payload: dict[str, Any]) -> ToolCallResponse:
    tools = _tool_definitions()
    if tool_name not in tools:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tool not found")
    if tool_name == "list_file_summaries":
        return _call_list_file_summaries(connection, payload)
    if tool_name == "read_text_file":
        return _call_read_text_file(connection, payload)
    if tool_name == "analyze_excel_file":
        return _call_analyze_excel_file(connection, payload)
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="tool is registered but not implemented")
