import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from sqlite3 import Connection, Row
from typing import Any
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, status

from app.schemas.excel import ExcelAnalysisRunRead, ExcelAnalyzeResponse
from app.services import llm as llm_service
from app.services.qa import get_answer
from app.services.tasks import get_task

ALLOWED_IMPORTS = {"pandas", "numpy", "json", "math", "statistics"}
BANNED_PATTERNS = [
    "import os",
    "import sys",
    "subprocess",
    "socket",
    "requests",
    "shutil",
    "pathlib",
    "eval(",
    "exec(",
    "__import__",
    "importlib",
]


@dataclass
class ExecutionResult:
    status: str
    result: dict[str, Any] | list[Any] | None
    stdout: str
    stderr: str
    error: str | None


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


def _run_row_to_read(row: Row) -> ExcelAnalysisRunRead:
    data = dict(row)
    data["result_json"] = json.loads(data["result_json"]) if data.get("result_json") else None
    return ExcelAnalysisRunRead(**data)


def _preview(value: str, limit: int = 700) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


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
        (question_id, task_id, question_text, "excel_analysis", _now_iso()),
    )
    return question_id


def _get_excel_source(connection: Connection, task_file_id: str) -> Row | None:
    return connection.execute(
        """
        SELECT
            tf.id AS task_file_id,
            tf.task_id,
            tf.physical_file_id,
            tf.display_name,
            pf.file_ext,
            pf.storage_path,
            pc.content_type,
            pc.excel_profile_json
        FROM task_files tf
        JOIN physical_files pf ON pf.id = tf.physical_file_id
        LEFT JOIN parsed_contents pc ON pc.task_file_id = tf.id
        WHERE tf.id = ?
        """,
        (task_file_id,),
    ).fetchone()


def _sheet_names(excel_profile: dict[str, Any]) -> list[str]:
    sheets = excel_profile.get("sheets") if isinstance(excel_profile.get("sheets"), list) else []
    return [str(sheet.get("sheet_name")) for sheet in sheets if isinstance(sheet, dict) and sheet.get("sheet_name")]


def _build_generation_prompt(question: str, sheet_name: str | None, excel_profile: dict[str, Any]) -> tuple[str, str]:
    system_prompt = (
        "You generate safe Python data-analysis code for a restricted sandbox. "
        "Return only valid JSON with analysis_plan, python_code, and expected_output_schema."
    )
    user_prompt = (
        "Generate Python code to answer the user's Excel analysis question.\n"
        "Rules:\n"
        "- The input file is exactly input.xlsx in the current working directory.\n"
        "- Write the final machine-readable result to exactly result.json.\n"
        "- Use Markdown-friendly plain values in result.json.\n"
        "- Allowed imports only: pandas, numpy, json, math, statistics.\n"
        "- Do not import os, sys, subprocess, socket, requests, shutil, pathlib, or importlib.\n"
        "- Do not use eval, exec, __import__.\n"
        "- open() may only be used as open('result.json', 'w', encoding='utf-8').\n"
        "- Prefer pandas.read_excel('input.xlsx', sheet_name=...).\n\n"
        "- For sales-performance questions, if columns like 单价 and 销售量 exist, calculate sales amount as 单价 * 销售量.\n"
        "- If targets are expressed in 万元, convert them to 元 before comparison.\n\n"
        "Return exactly this JSON schema:\n"
        '{"analysis_plan":"...","python_code":"...","expected_output_schema":{}}\n\n'
        f"User question:\n{question}\n\n"
        f"Requested sheet_name:\n{sheet_name or ''}\n\n"
        f"Excel profile JSON:\n{json.dumps(excel_profile, ensure_ascii=False)[:18000]}"
    )
    return system_prompt, user_prompt


def _build_repair_prompt(
    question: str,
    sheet_name: str | None,
    excel_profile: dict[str, Any],
    original_code: str,
    error_text: str,
) -> tuple[str, str]:
    system_prompt = (
        "You repair safe Python data-analysis code for a restricted sandbox. "
        "Return only valid JSON with analysis_plan, python_code, and expected_output_schema."
    )
    user_prompt = (
        "The previous code failed. Return repaired code that follows all sandbox rules.\n"
        "Rules:\n"
        "- The input file is exactly input.xlsx.\n"
        "- The code must write result.json.\n"
        "- Allowed imports only: pandas, numpy, json, math, statistics.\n"
        "- Do not import os, sys, subprocess, socket, requests, shutil, pathlib, or importlib.\n"
        "- Do not use eval, exec, __import__.\n"
        "- open() may only be used as open('result.json', 'w', encoding='utf-8').\n\n"
        "- For sales-performance questions, if columns like 单价 and 销售量 exist, calculate sales amount as 单价 * 销售量.\n"
        "- If targets are expressed in 万元, convert them to 元 before comparison.\n\n"
        "Return exactly this JSON schema:\n"
        '{"analysis_plan":"...","python_code":"...","expected_output_schema":{}}\n\n'
        f"User question:\n{question}\n\n"
        f"Requested sheet_name:\n{sheet_name or ''}\n\n"
        f"Execution error:\n{error_text[:4000]}\n\n"
        f"Original code:\n{original_code[:8000]}\n\n"
        f"Excel profile JSON:\n{json.dumps(excel_profile, ensure_ascii=False)[:14000]}"
    )
    return system_prompt, user_prompt


def _build_json_repair_prompt(raw_response: str) -> tuple[str, str]:
    system_prompt = (
        "You repair malformed JSON returned by an Excel code generator. "
        "Return only valid JSON with analysis_plan, python_code, and expected_output_schema."
    )
    user_prompt = (
        "The previous response could not be parsed as JSON. Convert it into valid JSON.\n"
        "Rules:\n"
        "- Preserve the intended Python code.\n"
        "- Escape newlines inside python_code as JSON string content.\n"
        "- Do not add markdown fences.\n"
        "- Return exactly this JSON schema:\n"
        '{"analysis_plan":"...","python_code":"...","expected_output_schema":{}}\n\n'
        f"Malformed response:\n{raw_response[:12000]}"
    )
    return system_prompt, user_prompt


def _parse_llm_code_response(text: str) -> tuple[str, str, dict[str, Any]]:
    payload = _extract_json_object(text)
    python_code = str(payload.get("python_code") or "").strip()
    analysis_plan = str(payload.get("analysis_plan") or "").strip()
    expected_output_schema = payload.get("expected_output_schema")
    if not python_code:
        raise ValueError("LLM JSON missing python_code")
    if not isinstance(expected_output_schema, dict):
        expected_output_schema = {}
    return analysis_plan, python_code, expected_output_schema


def _parse_or_repair_code_response(
    connection: Connection,
    *,
    task_id: str,
    agent_run_id: str | None,
    iteration_id: str | None,
    raw_response: str,
) -> tuple[str, str, dict[str, Any]]:
    try:
        return _parse_llm_code_response(raw_response)
    except Exception:
        repair_system_prompt, repair_user_prompt = _build_json_repair_prompt(raw_response)
        repair_result = llm_service.call_llm(
            connection,
            task_id=task_id,
            agent_run_id=agent_run_id,
            iteration_id=iteration_id,
            scenario="excel_code_repair",
            module_name="M10_EXCEL_SANDBOX_ANALYSIS",
            system_prompt=repair_system_prompt,
            user_prompt=repair_user_prompt,
        )
        return _parse_llm_code_response(repair_result.text)


def _string_constant_value(node: ast.AST, string_constants: dict[str, str]) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return string_constants.get(node.id)
    return None


def _collect_string_constants(tree: ast.AST) -> dict[str, str]:
    constants: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    constants[target.id] = node.value.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                constants[node.target.id] = node.value.value
    return constants


def _validate_open_call(node: ast.Call, string_constants: dict[str, str]) -> None:
    if not isinstance(node.func, ast.Name) or node.func.id != "open":
        return
    if not node.args or _string_constant_value(node.args[0], string_constants) != "result.json":
        raise ValueError("open() is only allowed for result.json")
    mode = "r"
    if len(node.args) >= 2:
        mode = str(_string_constant_value(node.args[1], string_constants) or "")
    for keyword in node.keywords:
        if keyword.arg == "mode":
            mode = str(_string_constant_value(keyword.value, string_constants) or "")
    if "w" not in mode or any(flag in mode for flag in ("r", "+", "a", "x")):
        raise ValueError("open() is only allowed in write mode for result.json")


def validate_python_code(code: str) -> None:
    lowered = code.lower()
    for pattern in BANNED_PATTERNS:
        if pattern in lowered:
            raise ValueError(f"banned code pattern: {pattern}")

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise ValueError(f"syntax error: {exc}") from exc

    string_constants = _collect_string_constants(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_name = alias.name.split(".")[0]
                if root_name not in ALLOWED_IMPORTS:
                    raise ValueError(f"import not allowed: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root_name = (node.module or "").split(".")[0]
            if root_name not in ALLOWED_IMPORTS:
                raise ValueError(f"import not allowed: {node.module}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "__import__"}:
                raise ValueError(f"call not allowed: {node.func.id}")
            _validate_open_call(node, string_constants)


def _prepare_input_xlsx(source_path: Path, file_ext: str, temp_dir: Path) -> None:
    target_path = temp_dir / "input.xlsx"
    if file_ext == "xlsx":
        shutil.copyfile(source_path, target_path)
    elif file_ext == "xls":
        data = pd.read_excel(source_path, sheet_name=None)
        with pd.ExcelWriter(target_path) as writer:
            for sheet_name, frame in data.items():
                frame.to_excel(writer, sheet_name=sheet_name[:31] or "Sheet1", index=False)
    elif file_ext == "csv":
        frame = pd.read_csv(source_path)
        with pd.ExcelWriter(target_path) as writer:
            frame.to_excel(writer, sheet_name="csv", index=False)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="task file is not an Excel-compatible file")


def _execute_code(source_path: Path, file_ext: str, code: str) -> ExecutionResult:
    with tempfile.TemporaryDirectory(prefix="knowledge_agent_excel_") as temp_name:
        temp_dir = Path(temp_name)
        _prepare_input_xlsx(source_path, file_ext, temp_dir)
        script_path = temp_dir / "analysis.py"
        script_path.write_text(code, encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        result_path = temp_dir / "result.json"
        stdout = completed.stdout
        stderr = completed.stderr
        if completed.returncode != 0:
            return ExecutionResult("failed", None, stdout, stderr, f"process exited with code {completed.returncode}")
        if not result_path.exists():
            return ExecutionResult("failed", None, stdout, stderr, "result.json was not created")
        try:
            result_payload = json.loads(result_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return ExecutionResult("failed", None, stdout, stderr, f"result.json is not valid JSON: {exc}")
        return ExecutionResult("success", result_payload, stdout, stderr, None)


def _execute_code_safely(source_path: Path, file_ext: str, code: str) -> ExecutionResult:
    try:
        return _execute_code(source_path, file_ext, code)
    except subprocess.TimeoutExpired as exc:
        return ExecutionResult("failed", None, exc.stdout or "", exc.stderr or "", "execution timed out after 10 seconds")
    except Exception as exc:
        return ExecutionResult("failed", None, "", "", str(exc))


def _insert_run(
    connection: Connection,
    *,
    task_id: str,
    agent_run_id: str | None,
    iteration_id: str | None,
    task_file_id: str,
    question_id: str,
    generated_code: str,
    final_code: str,
    code_status: str,
    execution_status: str,
    result_payload: dict[str, Any] | list[Any] | None,
    stdout: str | None,
    stderr: str | None,
    repair_attempts: int,
    first_error: str | None,
) -> str:
    run_id = f"excel_{uuid4().hex}"
    now = _now_iso()
    connection.execute(
        """
        INSERT INTO excel_analysis_runs (
            id,
            task_id,
            agent_run_id,
            iteration_id,
            task_file_id,
            question_id,
            generated_code,
            final_code,
            code_status,
            execution_status,
            result_json,
            stdout,
            stderr,
            repair_attempts,
            first_error,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            task_id,
            agent_run_id,
            iteration_id,
            task_file_id,
            question_id,
            generated_code,
            final_code,
            code_status,
            execution_status,
            json.dumps(result_payload, ensure_ascii=False) if result_payload is not None else None,
            stdout,
            stderr,
            repair_attempts,
            first_error,
            now,
            now,
        ),
    )
    return run_id


def _get_run(connection: Connection, run_id: str) -> ExcelAnalysisRunRead:
    row = connection.execute("SELECT * FROM excel_analysis_runs WHERE id = ?", (run_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="failed to save excel analysis run")
    return _run_row_to_read(row)


def _result_to_markdown(question: str, display_name: str, sheet_name: str | None, result_payload: Any) -> str:
    return (
        f"## Excel 分析结果\n\n"
        f"**问题**：{question}\n\n"
        f"**来源文件**：{display_name}\n\n"
        f"**Sheet**：{sheet_name or '未指定'}\n\n"
        f"```json\n{json.dumps(result_payload, ensure_ascii=False, indent=2)}\n```"
    )


def _insert_answer(
    connection: Connection,
    *,
    task_id: str,
    task_file_id: str,
    physical_file_id: str,
    display_name: str,
    question_id: str,
    question: str,
    answer_markdown: str,
    llm_provider: str,
    llm_model: str,
    iteration_count: int,
    run_id: str,
    agent_run_id: str | None,
) -> str:
    answer_id = f"ans_{uuid4().hex}"
    source_refs = [
        {
            "task_file_id": task_file_id,
            "physical_file_id": physical_file_id,
            "display_name": display_name,
            "score": 1.0,
            "matched_fields": ["selected_excel_file"],
            "reason": "用户在 Excel 分析页面显式选择该文件",
            "content_type": "excel",
            "chunk_refs": [{"type": "excel_analysis_run", "run_id": run_id}],
        }
    ]
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
            json.dumps([task_file_id], ensure_ascii=False),
            json.dumps(source_refs, ensure_ascii=False),
            iteration_count,
            llm_provider,
            llm_model,
            _now_iso(),
        ),
    )
    return answer_id


def analyze_excel_task_file(
    connection: Connection,
    task_file_id: str,
    question: str,
    sheet_name: str | None,
    agent_run_id: str | None = None,
    iteration_id: str | None = None,
) -> ExcelAnalyzeResponse:
    source = _get_excel_source(connection, task_file_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task file not found")
    task = get_task(connection, source["task_id"])
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    if source["content_type"] != "excel" or not source["excel_profile_json"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="task file has not been parsed as Excel")

    file_ext = str(source["file_ext"]).lower()
    if file_ext not in {"xlsx", "xls", "csv"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="task file is not Excel-compatible")
    storage_path = Path(source["storage_path"])
    if not storage_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="stored file not found")

    excel_profile = json.loads(source["excel_profile_json"])
    if sheet_name and sheet_name not in _sheet_names(excel_profile):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="sheet_name not found in parsed Excel profile")

    normalized_question = question.strip()
    question_id = _insert_question(connection, source["task_id"], normalized_question)
    system_prompt, user_prompt = _build_generation_prompt(normalized_question, sheet_name, excel_profile)
    llm_result = llm_service.call_llm(
        connection,
        task_id=source["task_id"],
        agent_run_id=agent_run_id,
        iteration_id=iteration_id,
        scenario="excel_code_generation",
        module_name="M10_EXCEL_SANDBOX_ANALYSIS",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    try:
        _, generated_code, _ = _parse_or_repair_code_response(
            connection,
            task_id=source["task_id"],
            agent_run_id=agent_run_id,
            iteration_id=iteration_id,
            raw_response=llm_result.text,
        )
    except Exception as exc:
        error_message = f"failed to parse generated code JSON: {exc}"
        run_id = _insert_run(
            connection,
            task_id=source["task_id"],
            agent_run_id=agent_run_id,
            iteration_id=iteration_id,
            task_file_id=task_file_id,
            question_id=question_id,
            generated_code="",
            final_code="",
            code_status="failed",
            execution_status="failed",
            result_payload=None,
            stdout="",
            stderr="",
            repair_attempts=0,
            first_error=error_message,
        )
        return ExcelAnalyzeResponse(run=_get_run(connection, run_id), answer=None)

    final_code = generated_code
    code_status = "passed"
    execution = ExecutionResult("failed", None, "", "", None)
    first_error = None
    repair_attempts = 0

    try:
        validate_python_code(final_code)
        execution = _execute_code_safely(storage_path, file_ext, final_code)
    except Exception as exc:
        code_status = "failed"
        execution = ExecutionResult("failed", None, "", "", str(exc))

    if execution.status != "success":
        first_error = "\n".join(part for part in [execution.error, execution.stderr] if part).strip() or "execution failed"
        repair_attempts = 1
        repair_system_prompt, repair_user_prompt = _build_repair_prompt(
            normalized_question,
            sheet_name,
            excel_profile,
            generated_code,
            first_error,
        )
        repair_result = llm_service.call_llm(
            connection,
            task_id=source["task_id"],
            agent_run_id=agent_run_id,
            iteration_id=iteration_id,
            scenario="excel_code_repair",
            module_name="M10_EXCEL_SANDBOX_ANALYSIS",
            system_prompt=repair_system_prompt,
            user_prompt=repair_user_prompt,
        )
        try:
            _, repaired_code, _ = _parse_or_repair_code_response(
                connection,
                task_id=source["task_id"],
                agent_run_id=agent_run_id,
                iteration_id=iteration_id,
                raw_response=repair_result.text,
            )
            final_code = repaired_code
            code_status = "passed"
            try:
                validate_python_code(final_code)
                execution = _execute_code_safely(storage_path, file_ext, final_code)
            except Exception as exc:
                code_status = "failed"
                execution = ExecutionResult("failed", None, "", "", str(exc))
        except Exception as exc:
            code_status = "failed"
            execution = ExecutionResult(
                "failed",
                None,
                execution.stdout,
                execution.stderr,
                f"failed to parse repaired code JSON: {exc}",
            )

    saved_first_error = first_error
    if execution.status != "success" and execution.error:
        saved_first_error = "\n".join(part for part in [first_error, execution.error] if part).strip()

    run_id = _insert_run(
        connection,
        task_id=source["task_id"],
        agent_run_id=agent_run_id,
        iteration_id=iteration_id,
        task_file_id=task_file_id,
        question_id=question_id,
        generated_code=generated_code,
        final_code=final_code,
        code_status=code_status,
        execution_status=execution.status,
        result_payload=execution.result,
        stdout=execution.stdout,
        stderr=execution.stderr,
        repair_attempts=repair_attempts,
        first_error=saved_first_error,
    )
    run = _get_run(connection, run_id)

    answer = None
    if execution.status == "success":
        answer_markdown = _result_to_markdown(normalized_question, source["display_name"], sheet_name, execution.result)
        answer_id = _insert_answer(
            connection,
            task_id=source["task_id"],
            task_file_id=task_file_id,
            physical_file_id=source["physical_file_id"],
            display_name=source["display_name"],
            question_id=question_id,
            question=normalized_question,
            answer_markdown=answer_markdown,
            llm_provider=llm_result.provider_type,
            llm_model=llm_result.model_name,
            iteration_count=task.iteration_count,
            run_id=run_id,
            agent_run_id=agent_run_id,
        )
        answer = get_answer(connection, answer_id)

    return ExcelAnalyzeResponse(run=run, answer=answer)
