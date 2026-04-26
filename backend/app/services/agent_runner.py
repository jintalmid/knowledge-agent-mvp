import json
from datetime import UTC, datetime
from sqlite3 import Connection, Row
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from app.schemas.agent_runner import AgentIterationRead, AgentRunRead, AgentRunStartResponse, ObservationRead
from app.services import llm as llm_service
from app.services import tool_registry
from app.services.tasks import get_task

PLAN_CONTEXT_LIMIT = 12000
FINAL_CONTEXT_LIMIT = 18000


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_loads(value: str | None, fallback: Any = None) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


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
    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("LLM response JSON must be an object")
    return parsed


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


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
        (question_id, task_id, question_text, "agent_run", _now_iso()),
    )
    return question_id


def _insert_agent_run(connection: Connection, task: Any, goal: str, max_iterations: int) -> str:
    now = _now_iso()
    agent_run_id = f"arun_{uuid4().hex}"
    connection.execute(
        """
        INSERT INTO agent_runs (
            id,
            task_id,
            goal,
            status,
            max_iterations,
            current_iteration,
            final_answer_markdown,
            stop_reason,
            owner_user_id,
            department_id,
            security_level,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            agent_run_id,
            task.id,
            goal,
            "running",
            max_iterations,
            0,
            None,
            None,
            task.owner_user_id,
            task.department_id,
            task.security_level,
            now,
            now,
        ),
    )
    return agent_run_id


def _insert_iteration(connection: Connection, agent_run_id: str, iteration_index: int) -> str:
    iteration_id = f"aiter_{uuid4().hex}"
    connection.execute(
        """
        INSERT INTO agent_iterations (
            id,
            agent_run_id,
            iteration_index,
            plan_text,
            tool_name,
            tool_input_json,
            tool_result_json,
            reflection_text,
            decision,
            llm_call_log_id,
            status,
            error_message,
            started_at,
            completed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            iteration_id,
            agent_run_id,
            iteration_index,
            None,
            None,
            None,
            None,
            None,
            "continue",
            None,
            "running",
            None,
            _now_iso(),
            None,
        ),
    )
    return iteration_id


def _update_iteration(
    connection: Connection,
    iteration_id: str,
    *,
    plan: dict[str, Any] | None = None,
    tool_name: str | None = None,
    tool_input: dict[str, Any] | None = None,
    tool_result: dict[str, Any] | None = None,
    reflection: dict[str, Any] | None = None,
    decision: str | None = None,
    llm_call_log_id: str | None = None,
    status_value: str | None = None,
    error_message: str | None = None,
    completed: bool = False,
) -> None:
    fields: dict[str, Any] = {}
    if plan is not None:
        fields["plan_text"] = _json_dumps(plan)
    if tool_name is not None:
        fields["tool_name"] = tool_name
    if tool_input is not None:
        fields["tool_input_json"] = _json_dumps(tool_input)
    if tool_result is not None:
        fields["tool_result_json"] = _json_dumps(tool_result)
    if reflection is not None:
        fields["reflection_text"] = _json_dumps(reflection)
    if decision is not None:
        fields["decision"] = decision
    if llm_call_log_id is not None:
        fields["llm_call_log_id"] = llm_call_log_id
    if status_value is not None:
        fields["status"] = status_value
    if error_message is not None:
        fields["error_message"] = error_message
    if completed:
        fields["completed_at"] = _now_iso()
    if not fields:
        return
    assignments = ", ".join(f"{field} = ?" for field in fields)
    connection.execute(f"UPDATE agent_iterations SET {assignments} WHERE id = ?", (*fields.values(), iteration_id))


def _update_agent_run(
    connection: Connection,
    agent_run_id: str,
    *,
    status_value: str | None = None,
    current_iteration: int | None = None,
    final_answer: str | None = None,
    stop_reason: str | None = None,
) -> None:
    fields: dict[str, Any] = {"updated_at": _now_iso()}
    if status_value is not None:
        fields["status"] = status_value
    if current_iteration is not None:
        fields["current_iteration"] = current_iteration
    if final_answer is not None:
        fields["final_answer_markdown"] = final_answer
    if stop_reason is not None:
        fields["stop_reason"] = stop_reason
    assignments = ", ".join(f"{field} = ?" for field in fields)
    connection.execute(f"UPDATE agent_runs SET {assignments} WHERE id = ?", (*fields.values(), agent_run_id))


def _file_summary_context(connection: Connection, task_id: str) -> tuple[list[dict[str, Any]], str]:
    rows = connection.execute(
        """
        SELECT
            tf.id AS task_file_id,
            tf.display_name,
            pf.file_ext,
            pc.content_type,
            fs.summary_text,
            fs.keywords_json,
            fs.tags_json,
            fs.category
        FROM task_files tf
        JOIN physical_files pf ON pf.id = tf.physical_file_id
        LEFT JOIN parsed_contents pc ON pc.task_file_id = tf.id
        LEFT JOIN file_summaries fs ON fs.task_file_id = tf.id
        WHERE tf.task_id = ?
        ORDER BY tf.created_at ASC
        """,
        (task_id,),
    ).fetchall()
    summaries: list[dict[str, Any]] = []
    for row in rows:
        summaries.append(
            {
                "file_id": row["task_file_id"],
                "display_name": row["display_name"],
                "file_ext": row["file_ext"],
                "content_type": row["content_type"],
                "summary": row["summary_text"] or "",
                "keywords": _json_loads(row["keywords_json"], []),
                "tags": _json_loads(row["tags_json"], []),
                "category": row["category"] or "",
            }
        )
    return summaries, _json_dumps(summaries)[:PLAN_CONTEXT_LIMIT]


def _observation_context(connection: Connection, agent_run_id: str) -> str:
    rows = connection.execute(
        """
        SELECT
            tool_name,
            observation_type,
            content_text,
            content_json,
            status,
            error_message,
            created_at
        FROM observations
        WHERE agent_run_id = ?
        ORDER BY created_at ASC
        """,
        (agent_run_id,),
    ).fetchall()
    observations = []
    for row in rows:
        observations.append(
            {
                "tool_name": row["tool_name"],
                "observation_type": row["observation_type"],
                "content_text": row["content_text"],
                "content_json": _json_loads(row["content_json"], {}),
                "status": row["status"],
                "error_message": row["error_message"],
            }
        )
    return _json_dumps(observations)[-PLAN_CONTEXT_LIMIT:]


def _history_context(connection: Connection, agent_run_id: str) -> str:
    iteration_rows = connection.execute(
        """
        SELECT
            id,
            iteration_index,
            plan_text,
            tool_name,
            tool_input_json,
            tool_result_json,
            reflection_text,
            decision,
            status,
            error_message
        FROM agent_iterations
        WHERE agent_run_id = ?
        ORDER BY iteration_index ASC
        """,
        (agent_run_id,),
    ).fetchall()
    observation_rows = connection.execute(
        """
        SELECT
            agent_iteration_id,
            tool_name,
            content_text,
            status,
            error_message
        FROM observations
        WHERE agent_run_id = ?
        ORDER BY created_at ASC
        """,
        (agent_run_id,),
    ).fetchall()
    observations_by_iteration: dict[str, list[dict[str, Any]]] = {}
    for row in observation_rows:
        observations_by_iteration.setdefault(row["agent_iteration_id"], []).append(
            {
                "tool_name": row["tool_name"],
                "content_text": row["content_text"],
                "status": row["status"],
                "error_message": row["error_message"],
            }
        )

    history = []
    for row in iteration_rows:
        history.append(
            {
                "iteration_index": row["iteration_index"],
                "selected_tool": row["tool_name"],
                "tool_input": _json_loads(row["tool_input_json"], {}),
                "tool_result": _json_loads(row["tool_result_json"], {}),
                "observations": observations_by_iteration.get(row["id"], []),
                "reflection": _json_loads(row["reflection_text"], {}),
                "decision": row["decision"],
                "status": row["status"],
                "error_message": row["error_message"],
            }
        )
    return _json_dumps(history)[-PLAN_CONTEXT_LIMIT:]


def _tools_context() -> str:
    return _json_dumps([tool.model_dump() for tool in tool_registry.list_tools()])


def _build_plan_prompt(
    question: str,
    file_summaries_json: str,
    history_json: str,
    tools_json: str,
    iteration_index: int,
    max_iterations: int,
) -> tuple[str, str]:
    system_prompt = (
        "You are the planning brain of a phase-0 ReAct Agent Runner. "
        "Choose exactly one next tool call or decide to stop. Return only valid JSON."
    )
    user_prompt = (
        "Create the next plan for this Agent run.\n"
        "Rules:\n"
        "- Use selected_tool = list_file_summaries when you need an overview.\n"
        "- Use read_text_file for parsed text files.\n"
        "- Use analyze_excel_file for parsed Excel or CSV-like files.\n"
        "- Use selected_tool = none only when should_stop is true.\n"
        "- selected_file_ids must contain task_file ids when a file-specific tool is selected.\n"
        "- Do not invent file ids.\n"
        "- Treat the latest reflection.next_step_hint as a strong instruction for this iteration.\n"
        "- If a tool failed for the same file in history, do not repeat that same tool/file pair unless the instruction is materially different.\n"
        "- When the question requires both targets/policies and actual metrics, inspect both kinds of files before stopping.\n"
        "- For questions containing 达标, 不达标, 目标, target, quota, KPI, or performance threshold, inspect target/policy/plan files when such files are available.\n"
        "- Return JSON only, no markdown.\n\n"
        "Required JSON schema:\n"
        "{"
        '"thought":"...",'
        '"selected_file_ids":["..."],'
        '"selected_tool":"list_file_summaries|read_text_file|analyze_excel_file|none",'
        '"tool_instruction":"...",'
        '"reason":"...",'
        '"should_stop":false'
        "}\n\n"
        f"Iteration: {iteration_index} of {max_iterations}\n"
        f"User question:\n{question}\n\n"
        f"File summaries:\n{file_summaries_json}\n\n"
        f"Historical observations and reflections:\n{history_json}\n\n"
        f"Available tools:\n{tools_json}"
    )
    return system_prompt, user_prompt


def _build_tool_input(
    plan: dict[str, Any],
    *,
    task_id: str,
    question: str,
    agent_run_id: str,
    iteration_id: str,
) -> tuple[str, dict[str, Any]]:
    selected_tool = str(plan.get("selected_tool") or "").strip()
    selected_file_ids = _string_list(plan.get("selected_file_ids"))
    instruction = str(plan.get("tool_instruction") or plan.get("reason") or "").strip()
    if selected_tool == "list_file_summaries":
        return selected_tool, {"task_id": task_id}
    if selected_tool in {"read_text_file", "analyze_excel_file"}:
        if not selected_file_ids:
            raise ValueError(f"{selected_tool} requires at least one selected_file_id")
        return selected_tool, {
            "task_id": task_id,
            "file_id": selected_file_ids[0],
            "question": question,
            "instruction": instruction or "Extract information that helps answer the user question.",
            "agent_run_id": agent_run_id,
            "iteration_id": iteration_id,
        }
    if selected_tool == "none" or bool(plan.get("should_stop")):
        return "none", {"task_id": task_id, "reason": str(plan.get("reason") or "")}
    raise ValueError(f"unsupported selected_tool: {selected_tool or '<empty>'}")


def _file_content_type(connection: Connection, task_id: str, file_id: str | None) -> str | None:
    if not file_id:
        return None
    row = connection.execute(
        """
        SELECT pc.content_type
        FROM task_files tf
        LEFT JOIN parsed_contents pc ON pc.task_file_id = tf.id
        WHERE tf.task_id = ? AND tf.id = ?
        """,
        (task_id, file_id),
    ).fetchone()
    if row is None:
        return None
    return row["content_type"]


def _coerce_tool_for_file_type(
    connection: Connection,
    *,
    task_id: str,
    tool_name: str,
    tool_input: dict[str, Any],
) -> str:
    file_id = tool_input.get("file_id")
    if not isinstance(file_id, str):
        return tool_name
    content_type = _file_content_type(connection, task_id, file_id)
    if tool_name == "read_text_file" and content_type == "excel":
        return "analyze_excel_file"
    if tool_name == "analyze_excel_file" and content_type == "text":
        return "read_text_file"
    return tool_name


def _call_tool_safely(connection: Connection, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "none":
        return {
            "tool_name": "none",
            "status": "skipped",
            "output": {"observation": "Planner decided no tool call is needed before stopping."},
        }
    try:
        response = tool_registry.call_tool(connection, tool_name, tool_input)
        return response.model_dump()
    except HTTPException as exc:
        return {
            "tool_name": tool_name,
            "status": "failed",
            "output": {},
            "error_message": str(exc.detail),
        }
    except Exception as exc:
        return {
            "tool_name": tool_name,
            "status": "failed",
            "output": {},
            "error_message": str(exc),
        }


def _has_failed_tool_file_pair(
    connection: Connection,
    *,
    agent_run_id: str,
    tool_name: str,
    file_id: str | None,
) -> bool:
    if not file_id:
        return False
    rows = connection.execute(
        """
        SELECT tool_input_json, tool_result_json
        FROM agent_iterations
        WHERE agent_run_id = ? AND tool_name = ?
        """,
        (agent_run_id, tool_name),
    ).fetchall()
    for row in rows:
        tool_input = _json_loads(row["tool_input_json"], {})
        tool_result = _json_loads(row["tool_result_json"], {})
        if tool_input.get("file_id") == file_id and tool_result.get("status") == "failed":
            return True
    return False


def _blocked_repeat_tool_result(tool_name: str, file_id: str | None) -> dict[str, Any]:
    return {
        "tool_name": tool_name,
        "status": "failed",
        "output": {
            "observation": (
                "Repeated failed tool/file pair was blocked by Agent Runner. "
                "Choose a different file, a different tool, or a materially different instruction."
            ),
            "file_id": file_id,
        },
        "error_message": "repeated failed tool/file pair blocked",
    }


def _observation_text_from_tool_result(tool_result: dict[str, Any]) -> str:
    output = tool_result.get("output")
    if isinstance(output, dict):
        observation = output.get("observation")
        if isinstance(observation, str) and observation.strip():
            return observation.strip()
        summaries = output.get("summaries")
        if isinstance(summaries, list):
            return f"Listed {len(summaries)} file summaries."
        result_json = output.get("result_json")
        if result_json is not None:
            return f"Tool returned result_json: {_json_dumps(result_json)[:1200]}"
    if tool_result.get("error_message"):
        return str(tool_result["error_message"])
    return f"Tool {tool_result.get('tool_name', 'unknown')} finished with status {tool_result.get('status', 'unknown')}."


def _insert_observation(
    connection: Connection,
    *,
    agent_run_id: str,
    iteration_id: str,
    tool_name: str,
    tool_result: dict[str, Any],
) -> str:
    observation_id = f"obs_{uuid4().hex}"
    status_value = str(tool_result.get("status") or "unknown")
    error_message = tool_result.get("error_message")
    connection.execute(
        """
        INSERT INTO observations (
            id,
            agent_run_id,
            agent_iteration_id,
            tool_name,
            observation_type,
            content_text,
            content_json,
            status,
            error_message,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            observation_id,
            agent_run_id,
            iteration_id,
            tool_name,
            "tool_result",
            _observation_text_from_tool_result(tool_result),
            _json_dumps(tool_result),
            status_value,
            error_message,
            _now_iso(),
        ),
    )
    return observation_id


def _build_reflection_prompt(
    question: str,
    file_summaries_json: str,
    plan: dict[str, Any],
    tool_result: dict[str, Any],
) -> tuple[str, str]:
    system_prompt = (
        "You are the reflection brain of a phase-0 ReAct Agent Runner. "
        "Judge whether the latest observation is enough to answer. Return only valid JSON."
    )
    user_prompt = (
        "Reflect on the latest tool result.\n"
        "Decision rules:\n"
        "- Use decision = stop when the observations are enough, no useful tool remains, or the plan said should_stop=true.\n"
        "- Use decision = continue when another tool call is likely to improve the answer.\n"
        "- If tool_result.status is success and output.result_json is present, treat that result as valid evidence.\n"
        "- If the question asks whether something met a target/threshold but the latest result only provides actual metrics, decision must be continue when target/policy/plan files are available.\n"
        "- For 达标/不达标/目标 questions, do not treat lowest or highest actual value as target compliance unless an explicit target or rule has been observed.\n"
        "- Do not require perfect certainty; explicitly list missing information if any.\n\n"
        "Required JSON schema:\n"
        "{"
        '"reflection":"...",'
        '"is_enough":true,'
        '"missing_information":["..."],'
        '"next_step_hint":"...",'
        '"decision":"continue|stop"'
        "}\n\n"
        f"User question:\n{question}\n\n"
        f"Available file summaries:\n{file_summaries_json}\n\n"
        f"Plan:\n{_json_dumps(plan)}\n\n"
        f"Tool result:\n{_json_dumps(tool_result)[:PLAN_CONTEXT_LIMIT]}"
    )
    return system_prompt, user_prompt


def _source_refs_for_answer(connection: Connection, task_id: str, selected_file_ids: list[str]) -> list[dict[str, Any]]:
    if not selected_file_ids:
        return []
    unique_ids = list(dict.fromkeys(selected_file_ids))
    placeholders = ",".join("?" for _ in unique_ids)
    rows = connection.execute(
        f"""
        SELECT
            tf.id AS task_file_id,
            tf.physical_file_id,
            tf.display_name,
            pc.content_type
        FROM task_files tf
        LEFT JOIN parsed_contents pc ON pc.task_file_id = tf.id
        WHERE tf.task_id = ? AND tf.id IN ({placeholders})
        """,
        (task_id, *unique_ids),
    ).fetchall()
    by_id = {row["task_file_id"]: row for row in rows}
    refs = []
    for task_file_id in unique_ids:
        row = by_id.get(task_file_id)
        if row is None:
            continue
        refs.append(
            {
                "task_file_id": row["task_file_id"],
                "physical_file_id": row["physical_file_id"],
                "display_name": row["display_name"],
                "score": 1.0,
                "matched_fields": ["agent_observation"],
                "reason": "Selected and used by Agent Runner.",
                "content_type": row["content_type"] or "unknown",
                "chunk_refs": [],
            }
        )
    return refs


def _selected_file_ids_from_iterations(iterations: list[dict[str, Any]]) -> list[str]:
    selected: list[str] = []
    for item in iterations:
        plan = item.get("plan") or {}
        selected.extend(_string_list(plan.get("selected_file_ids")))
        tool_input = item.get("tool_input") or {}
        file_id = tool_input.get("file_id")
        if isinstance(file_id, str) and file_id.strip():
            selected.append(file_id.strip())
        tool_result = item.get("tool_result") or {}
        output = tool_result.get("output") if isinstance(tool_result, dict) else None
        if isinstance(output, dict):
            output_file_id = output.get("file_id")
            if isinstance(output_file_id, str) and output_file_id.strip():
                selected.append(output_file_id.strip())
            summaries = output.get("summaries")
            if isinstance(summaries, list):
                for summary in summaries:
                    if isinstance(summary, dict):
                        summary_file_id = summary.get("file_id") or summary.get("task_file_id")
                        if isinstance(summary_file_id, str) and summary_file_id.strip():
                            selected.append(summary_file_id.strip())
    return list(dict.fromkeys(selected))


def _build_final_prompt(question: str, iterations: list[dict[str, Any]]) -> tuple[str, str]:
    system_prompt = (
        "You are the final answer writer for an enterprise ReAct Agent. "
        "Answer only from observations collected by tools. Output Markdown only."
    )
    user_prompt = (
        "Write the final answer for the user.\n"
        "Requirements:\n"
        "- Directly answer the question.\n"
        "- Mention which files or observations support the answer.\n"
        "- If information is missing or uncertain, say so clearly.\n"
        "- Do not invent facts outside the observations.\n"
        "- A successful tool_result with output.result_json is valid evidence even if the tool needed a repair attempt before succeeding.\n"
        "- When both target observations and actual metric result_json are present, synthesize them instead of treating later missing-information reflections as the whole result.\n"
        "- Output Markdown only.\n\n"
        f"User question:\n{question}\n\n"
        f"Agent iterations and observations:\n{_json_dumps(iterations)[-FINAL_CONTEXT_LIMIT:]}"
    )
    return system_prompt, user_prompt


def _insert_answer(
    connection: Connection,
    *,
    task_id: str,
    question_id: str,
    agent_run_id: str,
    answer_markdown: str,
    selected_file_ids: list[str],
    source_refs: list[dict[str, Any]],
    iteration_count: int,
    provider_type: str,
    model_name: str,
) -> str:
    answer_id = f"ans_{uuid4().hex}"
    connection.execute(
        """
        INSERT INTO answers (
            id,
            task_id,
            agent_run_id,
            question_id,
            answer_text_markdown,
            selected_task_file_ids_json,
            source_refs_json,
            iteration_count,
            llm_provider,
            llm_model,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            answer_id,
            task_id,
            agent_run_id,
            question_id,
            answer_markdown,
            _json_dumps(selected_file_ids),
            _json_dumps(source_refs),
            iteration_count,
            provider_type,
            model_name,
            _now_iso(),
        ),
    )
    return answer_id


def _observation_row_to_read(row: Row) -> ObservationRead:
    data = dict(row)
    data["content_json"] = _json_loads(data["content_json"], {})
    return ObservationRead(**data)


def _iteration_row_to_read(row: Row, observations: list[ObservationRead]) -> AgentIterationRead:
    data = dict(row)
    data["plan_text"] = _json_loads(data["plan_text"], None)
    data["tool_input_json"] = _json_loads(data["tool_input_json"], None)
    data["tool_result_json"] = _json_loads(data["tool_result_json"], None)
    data["reflection_text"] = _json_loads(data["reflection_text"], None)
    data["observations"] = observations
    return AgentIterationRead(**data)


def get_agent_run(connection: Connection, run_id: str) -> AgentRunRead | None:
    run_row = connection.execute("SELECT * FROM agent_runs WHERE id = ?", (run_id,)).fetchone()
    if run_row is None:
        return None

    iteration_rows = connection.execute(
        """
        SELECT *
        FROM agent_iterations
        WHERE agent_run_id = ?
        ORDER BY iteration_index ASC
        """,
        (run_id,),
    ).fetchall()
    observation_rows = connection.execute(
        """
        SELECT *
        FROM observations
        WHERE agent_run_id = ?
        ORDER BY created_at ASC
        """,
        (run_id,),
    ).fetchall()
    observations_by_iteration: dict[str, list[ObservationRead]] = {}
    for row in observation_rows:
        observation = _observation_row_to_read(row)
        observations_by_iteration.setdefault(observation.agent_iteration_id, []).append(observation)

    run_data = dict(run_row)
    run_data["iterations"] = [
        _iteration_row_to_read(row, observations_by_iteration.get(row["id"], [])) for row in iteration_rows
    ]
    return AgentRunRead(**run_data)


def start_agent_run(connection: Connection, task_id: str, question: str, max_iterations: int) -> AgentRunStartResponse:
    task = get_task(connection, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")

    normalized_question = question.strip()
    max_iterations = max(1, min(max_iterations, 10))
    question_id = _insert_question(connection, task_id, normalized_question)
    agent_run_id = _insert_agent_run(connection, task, normalized_question, max_iterations)
    connection.commit()

    iterations_for_final: list[dict[str, Any]] = []
    final_decision = "max_iterations"
    final_answer = ""
    answer_id: str | None = None

    try:
        for iteration_index in range(1, max_iterations + 1):
            iteration_id = _insert_iteration(connection, agent_run_id, iteration_index)
            connection.commit()

            _, file_summaries_json = _file_summary_context(connection, task_id)
            history_json = _history_context(connection, agent_run_id)
            plan_system_prompt, plan_user_prompt = _build_plan_prompt(
                normalized_question,
                file_summaries_json,
                history_json,
                _tools_context(),
                iteration_index,
                max_iterations,
            )
            plan_llm = llm_service.call_llm(
                connection,
                task_id=task_id,
                agent_run_id=agent_run_id,
                iteration_id=iteration_id,
                module_name="M07_V03_AGENT_RUNNER_PLAN",
                system_prompt=plan_system_prompt,
                user_prompt=plan_user_prompt,
            )
            try:
                plan = _extract_json_object(plan_llm.text)
            except Exception as exc:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Agent plan JSON parse failed: {exc}") from exc

            try:
                tool_name, tool_input = _build_tool_input(
                    plan,
                    task_id=task_id,
                    question=normalized_question,
                    agent_run_id=agent_run_id,
                    iteration_id=iteration_id,
                )
            except ValueError as exc:
                tool_name = str(plan.get("selected_tool") or "unknown")
                tool_input = {}
                tool_result = {
                    "tool_name": tool_name,
                    "status": "failed",
                    "output": {},
                    "error_message": str(exc),
                }
            else:
                tool_name = _coerce_tool_for_file_type(
                    connection,
                    task_id=task_id,
                    tool_name=tool_name,
                    tool_input=tool_input,
                )
                file_id = tool_input.get("file_id")
                if isinstance(file_id, str) and _has_failed_tool_file_pair(
                    connection,
                    agent_run_id=agent_run_id,
                    tool_name=tool_name,
                    file_id=file_id,
                ):
                    tool_result = _blocked_repeat_tool_result(tool_name, file_id)
                else:
                    tool_result = _call_tool_safely(connection, tool_name, tool_input)

            _insert_observation(
                connection,
                agent_run_id=agent_run_id,
                iteration_id=iteration_id,
                tool_name=tool_name,
                tool_result=tool_result,
            )

            reflection_system_prompt, reflection_user_prompt = _build_reflection_prompt(
                normalized_question,
                file_summaries_json,
                plan,
                tool_result,
            )
            reflection_llm = llm_service.call_llm(
                connection,
                task_id=task_id,
                agent_run_id=agent_run_id,
                iteration_id=iteration_id,
                module_name="M08_V03_REACT_REFLECTION",
                system_prompt=reflection_system_prompt,
                user_prompt=reflection_user_prompt,
            )
            try:
                reflection = _extract_json_object(reflection_llm.text)
            except Exception as exc:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Agent reflection JSON parse failed: {exc}") from exc

            decision = str(reflection.get("decision") or "").strip().lower()
            if decision not in {"continue", "stop"}:
                decision = "stop" if bool(reflection.get("is_enough")) else "continue"
            if bool(plan.get("should_stop")):
                decision = "stop"

            _update_iteration(
                connection,
                iteration_id,
                plan=plan,
                tool_name=tool_name,
                tool_input=tool_input,
                tool_result=tool_result,
                reflection=reflection,
                decision=decision,
                llm_call_log_id=plan_llm.log_id,
                status_value="completed",
                completed=True,
            )
            _update_agent_run(connection, agent_run_id, current_iteration=iteration_index)
            connection.commit()

            iterations_for_final.append(
                {
                    "iteration_id": iteration_id,
                    "iteration_index": iteration_index,
                    "plan": plan,
                    "tool_input": tool_input,
                    "tool_result": tool_result,
                    "reflection": reflection,
                    "decision": decision,
                }
            )

            if decision == "stop":
                final_decision = "reflection_stop"
                break

        iteration_count = len(iterations_for_final)
        final_system_prompt, final_user_prompt = _build_final_prompt(normalized_question, iterations_for_final)
        final_llm = llm_service.call_llm(
            connection,
            task_id=task_id,
            agent_run_id=agent_run_id,
            iteration_id=None,
            module_name="M07_V03_AGENT_FINAL_ANSWER",
            system_prompt=final_system_prompt,
            user_prompt=final_user_prompt,
        )
        final_answer = final_llm.text
        selected_file_ids = _selected_file_ids_from_iterations(iterations_for_final)
        source_refs = _source_refs_for_answer(connection, task_id, selected_file_ids)
        answer_id = _insert_answer(
            connection,
            task_id=task_id,
            question_id=question_id,
            agent_run_id=agent_run_id,
            answer_markdown=final_answer,
            selected_file_ids=selected_file_ids,
            source_refs=source_refs,
            iteration_count=iteration_count,
            provider_type=final_llm.provider_type,
            model_name=final_llm.model_name,
        )
        _update_agent_run(
            connection,
            agent_run_id,
            status_value="completed",
            current_iteration=iteration_count,
            final_answer=final_answer,
            stop_reason=final_decision,
        )
        return AgentRunStartResponse(
            agent_run_id=agent_run_id,
            answer_id=answer_id,
            status="completed",
            iteration_count=iteration_count,
        )
    except HTTPException as exc:
        _update_agent_run(connection, agent_run_id, status_value="failed", stop_reason=str(exc.detail))
        connection.commit()
        raise
    except Exception as exc:
        _update_agent_run(connection, agent_run_id, status_value="failed", stop_reason=str(exc))
        connection.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
