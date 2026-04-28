"""Legacy v0.2 phase-0 capability check service.

The current M12 target is a v0.3 Agent Runner capability check centered on
agent_runs, agent_iterations, observations, answers.agent_run_id, and
llm_call_logs agent associations.

This module remains available for the existing /modules/capability-check page
until M12 is migrated. Keep changes here compatibility-focused.
"""

import json
from sqlite3 import Connection

from app.schemas.capability import CapabilityCheckRead, CapabilityStepRead, Phase0RequirementRead, Phase0RequirementsRead

PHASE = "phase_0"

PHASE0_REQUIREMENTS = [
    {
        "step": "task_created",
        "description": "已创建临时任务空间。",
        "module_ids": ["M02"],
        "recommended_page": "/tasks",
    },
    {
        "step": "file_uploaded",
        "description": "任务中已上传至少一个阶段 0 支持的文件。",
        "module_ids": ["M03", "M04"],
        "recommended_page": "/tasks/{task_id}/files",
    },
    {
        "step": "physical_file_deduplicated",
        "description": "上传文件已落到 physical_files，并通过 content_hash 支撑 SHA256 去重。",
        "module_ids": ["M03"],
        "recommended_page": "/tasks/{task_id}/files",
    },
    {
        "step": "task_file_reference_created",
        "description": "任务文件引用已创建，且与物理文件资产解耦。",
        "module_ids": ["M04"],
        "recommended_page": "/tasks/{task_id}/files",
    },
    {
        "step": "file_parsed",
        "description": "任务内至少一个文件完成解析。",
        "module_ids": ["M05"],
        "recommended_page": "/tasks/{task_id}/parsing",
    },
    {
        "step": "summary_generated",
        "description": "任务内至少一个文件完成 LLM 摘要与标签生成。",
        "module_ids": ["M06"],
        "recommended_page": "/tasks/{task_id}/summaries",
    },
    {
        "step": "retrieval_available",
        "description": "临时检索已有可用上下文，来自摘要或 chunk。",
        "module_ids": ["M07", "M08"],
        "recommended_page": "/tasks/{task_id}/retrieval",
    },
    {
        "step": "text_answer_generated_or_excel_analysis_generated",
        "description": "已生成文本问答结果，或已成功完成 Excel 沙箱分析。",
        "module_ids": ["M09", "M10"],
        "recommended_page": "/tasks/{task_id}/ask",
    },
    {
        "step": "result_has_sources",
        "description": "保存的结果包含来源文件引用。",
        "module_ids": ["M11"],
        "recommended_page": "/tasks/{task_id}/results",
    },
    {
        "step": "llm_logs_available",
        "description": "任务相关 LLM 调用已写入日志。",
        "module_ids": ["M13"],
        "recommended_page": "/debug/llm-logs",
    },
]


def _count(connection: Connection, query: str, params: tuple = ()) -> int:
    row = connection.execute(query, params).fetchone()
    return int(row[0] if row is not None else 0)


def _step(step: str, status: str, message: str, next_page: str | None) -> CapabilityStepRead:
    return CapabilityStepRead(step=step, status=status, message=message, next_page=next_page)


def _page(path: str, task_id: str) -> str:
    return path.format(task_id=task_id)


def _has_sources(connection: Connection, task_id: str) -> bool:
    rows = connection.execute("SELECT source_refs_json FROM answers WHERE task_id = ?", (task_id,)).fetchall()
    for row in rows:
        try:
            source_refs = json.loads(row["source_refs_json"] or "[]")
        except json.JSONDecodeError:
            continue
        if isinstance(source_refs, list) and source_refs:
            return True
    return False


def get_phase0_requirements() -> Phase0RequirementsRead:
    return Phase0RequirementsRead(
        phase=PHASE,
        requirements=[Phase0RequirementRead(**requirement) for requirement in PHASE0_REQUIREMENTS],
    )


def check_task_capability(connection: Connection, task_id: str) -> CapabilityCheckRead:
    task_count = _count(connection, "SELECT COUNT(*) FROM tasks WHERE id = ?", (task_id,))
    if task_count == 0:
        return CapabilityCheckRead(
            task_id=task_id,
            phase=PHASE,
            steps=[
                _step("task_created", "failed", "未找到该任务空间。", "/tasks"),
            ],
            overall_status="failed",
        )

    task_file_count = _count(connection, "SELECT COUNT(*) FROM task_files WHERE task_id = ?", (task_id,))
    physical_join_count = _count(
        connection,
        """
        SELECT COUNT(*)
        FROM task_files tf
        JOIN physical_files pf ON pf.id = tf.physical_file_id
        WHERE tf.task_id = ? AND pf.content_hash IS NOT NULL AND pf.content_hash != ''
        """,
        (task_id,),
    )
    parsed_count = _count(
        connection,
        """
        SELECT COUNT(*)
        FROM parsed_contents pc
        JOIN task_files tf ON tf.id = pc.task_file_id
        WHERE tf.task_id = ?
        """,
        (task_id,),
    )
    parse_failed_count = _count(connection, "SELECT COUNT(*) FROM task_files WHERE task_id = ? AND parse_status = 'failed'", (task_id,))
    summary_count = _count(
        connection,
        """
        SELECT COUNT(*)
        FROM file_summaries fs
        JOIN task_files tf ON tf.id = fs.task_file_id
        WHERE tf.task_id = ?
        """,
        (task_id,),
    )
    summary_failed_count = _count(connection, "SELECT COUNT(*) FROM task_files WHERE task_id = ? AND summary_status = 'failed'", (task_id,))
    chunk_count = _count(
        connection,
        """
        SELECT COUNT(*)
        FROM document_chunks dc
        JOIN task_files tf ON tf.id = dc.task_file_id
        WHERE tf.task_id = ?
        """,
        (task_id,),
    )
    text_answer_count = _count(
        connection,
        """
        SELECT COUNT(*)
        FROM answers a
        JOIN questions q ON q.id = a.question_id
        WHERE a.task_id = ? AND q.question_type = 'text_qa'
        """,
        (task_id,),
    )
    excel_success_count = _count(
        connection,
        "SELECT COUNT(*) FROM excel_analysis_runs WHERE task_id = ? AND execution_status = 'success'",
        (task_id,),
    )
    excel_failed_count = _count(
        connection,
        "SELECT COUNT(*) FROM excel_analysis_runs WHERE task_id = ? AND execution_status = 'failed'",
        (task_id,),
    )
    llm_log_count = _count(connection, "SELECT COUNT(*) FROM llm_call_logs WHERE task_id = ?", (task_id,))

    steps: list[CapabilityStepRead] = []
    steps.append(_step("task_created", "passed", "任务空间已创建。", _page("/tasks/{task_id}", task_id)))

    if task_file_count > 0:
        steps.append(_step("file_uploaded", "passed", f"已上传 {task_file_count} 个任务文件。", _page("/tasks/{task_id}/files", task_id)))
    else:
        steps.append(_step("file_uploaded", "missing", "尚未上传文件。", _page("/tasks/{task_id}/files", task_id)))

    if task_file_count == 0:
        steps.append(_step("physical_file_deduplicated", "missing", "尚无文件可检查 SHA256 去重。", _page("/tasks/{task_id}/files", task_id)))
    elif physical_join_count == task_file_count:
        steps.append(
            _step(
                "physical_file_deduplicated",
                "passed",
                "所有任务文件均关联 physical_files，且存在 content_hash。",
                _page("/tasks/{task_id}/files", task_id),
            )
        )
    else:
        steps.append(_step("physical_file_deduplicated", "failed", "存在任务文件未正确关联物理文件或 content_hash。", _page("/tasks/{task_id}/files", task_id)))

    if task_file_count > 0:
        steps.append(_step("task_file_reference_created", "passed", "任务文件引用已创建。", _page("/tasks/{task_id}/files", task_id)))
    else:
        steps.append(_step("task_file_reference_created", "missing", "尚未创建任务文件引用。", _page("/tasks/{task_id}/files", task_id)))

    if parsed_count > 0:
        steps.append(_step("file_parsed", "passed", f"已有 {parsed_count} 个文件完成解析。", _page("/tasks/{task_id}/parsing", task_id)))
    elif parse_failed_count > 0:
        steps.append(_step("file_parsed", "failed", "存在解析失败的文件，且尚无成功解析结果。", _page("/tasks/{task_id}/parsing", task_id)))
    else:
        steps.append(_step("file_parsed", "missing", "尚未完成文件解析。", _page("/tasks/{task_id}/parsing", task_id)))

    if summary_count > 0:
        steps.append(_step("summary_generated", "passed", f"已有 {summary_count} 个文件生成摘要。", _page("/tasks/{task_id}/summaries", task_id)))
    elif summary_failed_count > 0:
        steps.append(_step("summary_generated", "failed", "存在摘要生成失败记录，且尚无成功摘要。", _page("/tasks/{task_id}/summaries", task_id)))
    else:
        steps.append(_step("summary_generated", "missing", "尚未生成文件摘要。", _page("/tasks/{task_id}/summaries", task_id)))

    if summary_count > 0 or chunk_count > 0:
        steps.append(
            _step(
                "retrieval_available",
                "passed",
                f"检索上下文可用：摘要 {summary_count} 条，chunk {chunk_count} 条。",
                _page("/tasks/{task_id}/retrieval", task_id),
            )
        )
    else:
        steps.append(_step("retrieval_available", "missing", "尚无摘要或 chunk 可供临时检索。", _page("/tasks/{task_id}/retrieval", task_id)))

    if text_answer_count > 0 or excel_success_count > 0:
        steps.append(
            _step(
                "text_answer_generated_or_excel_analysis_generated",
                "passed",
                f"已生成文本答案 {text_answer_count} 条，成功 Excel 分析 {excel_success_count} 次。",
                _page("/tasks/{task_id}/results", task_id),
            )
        )
    elif excel_failed_count > 0:
        steps.append(
            _step(
                "text_answer_generated_or_excel_analysis_generated",
                "failed",
                "存在 Excel 分析失败记录，且尚无文本答案或成功 Excel 分析。",
                _page("/tasks/{task_id}/excel", task_id),
            )
        )
    else:
        steps.append(
            _step(
                "text_answer_generated_or_excel_analysis_generated",
                "missing",
                "尚未生成文本答案或成功 Excel 分析。",
                _page("/tasks/{task_id}/ask", task_id),
            )
        )

    if _has_sources(connection, task_id):
        steps.append(_step("result_has_sources", "passed", "已有结果包含来源文件引用。", _page("/tasks/{task_id}/results", task_id)))
    else:
        steps.append(_step("result_has_sources", "missing", "尚无带来源引用的结果。", _page("/tasks/{task_id}/results", task_id)))

    if llm_log_count > 0:
        steps.append(_step("llm_logs_available", "passed", f"任务已有 {llm_log_count} 条 LLM 调用日志。", "/debug/llm-logs"))
    else:
        steps.append(_step("llm_logs_available", "missing", "尚无任务相关 LLM 调用日志。", "/settings/llm"))

    statuses = [step.status for step in steps]
    if "failed" in statuses:
        overall_status = "failed"
    elif all(status == "passed" for status in statuses):
        overall_status = "ready"
    else:
        overall_status = "incomplete"

    return CapabilityCheckRead(task_id=task_id, phase=PHASE, steps=steps, overall_status=overall_status)
