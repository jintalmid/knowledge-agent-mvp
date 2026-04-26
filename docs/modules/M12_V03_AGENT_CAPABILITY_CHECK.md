# M12 v0.3 能力盘点

## 模块目标

将原 v0.2 的阶段 0 能力检查迁移为 v0.3 Agent Runner 能力盘点。当前注册表中该模块仍标记为 planned，但已有兼容的能力检查页面和 API。

## 当前已有能力

API：

- `GET /api/tasks/{task_id}/capability-check`
- `GET /api/phase0/requirements`

页面：

- `/modules/capability-check`

## 当前检查项

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
