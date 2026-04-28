# M12 v0.3 能力盘点

## 模块目标

将原 v0.2 的阶段 0 能力检查迁移为 v0.3 Agent Runner 能力盘点。当前注册表中该模块仍标记为 planned。

当前已有页面和 API 仍是 legacy compatibility，用于观察旧流程完整度；它们不是 v0.3 的最终调用契约。

## 当前 Legacy 兼容能力

API：

- `GET /api/tasks/{task_id}/capability-check`
- `GET /api/phase0/requirements`

页面：

- `/modules/capability-check`

## 当前 Legacy 检查项

- `task_created`
- `file_uploaded`
- `physical_file_deduplicated`
- `task_file_reference_created`
- `file_parsed`
- `summary_generated`
- `retrieval_available`
- `text_answer_generated` 或 `excel_analysis_generated`
- `result_has_sources`
- `llm_logs_available`

## v0.3 目标检查项

后续应迁移为：

- task exists。
- LLM configured。
- file context available。
- file parsed。
- file summarized。
- tools registered。
- agent_run_created。
- agent_iterations_created。
- observations_created。
- final_answer_saved。
- llm_logs_linked_to_agent_run。

## 迁移输入

- `backend/app/services/capability.py`：旧版 phase 0 检查，保留现有页面使用。
- `backend/app/services/retrieval.py`：旧版 retrieval/chunk 检查来源，可作为 file context available 的参考，但不再定义主流程。
- `backend/app/services/qa.py`：旧版 `/ask` 文本问答，结果表结构仍复用 `answers`，但 v0.3 应优先检查 `answers.agent_run_id`。

## 响应格式

```json
{
  "task_id": "task_xxx",
  "phase": "phase_0",
  "steps": [
    {
      "step": "task_created",
      "status": "passed|missing|failed",
      "message": "...",
      "next_page": "..."
    }
  ],
  "overall_status": "ready|incomplete|failed"
}
```

## 非目标

- 不做自动修复。
- 不做后台巡检。
- 不做生产健康监控。
