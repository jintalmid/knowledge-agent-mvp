# M13 v0.3 Debug 与历史日志

## 模块目标

提供 LLM 调用日志和 Debug 信息，辅助定位摘要、工具、Excel 分析和 Agent Runner 的问题。

## 当前实现

- 所有 LLM 调用写入 `llm_call_logs`。
- 日志可关联 `task_id`、`agent_run_id`、`iteration_id`。
- 日志记录 `scenario`、`provider_id`、`model_id`，用于排查模型路由。
- Debug 页面展示最近日志。
- 日志详情可查看 prompt preview、response preview、错误和耗时。

## 数据表

`llm_call_logs`：

- `id`
- `task_id`
- `agent_run_id`
- `iteration_id`
- `scenario`
- `provider_id`
- `model_id`
- `module_name`
- `provider_type`
- `model_name`
- `prompt_preview`
- `response_preview`
- `status`
- `error_message`
- `latency_ms`
- `created_at`

## API

- `GET /api/llm-logs`
- `GET /api/llm-logs/{log_id}`

## 页面

- `/debug/llm-logs`

## 常见排查路径

Agent Run 失败时：

1. 打开 `/tasks/{taskId}/runs/{runId}` 查看每轮 plan、tool result、reflection。
2. 打开 `/debug/llm-logs` 查看关联的 LLM 调用。
3. 检查 `module_name`：
   - `M07_V03_AGENT_RUNNER_PLAN`
   - `M08_V03_REACT_REFLECTION`
   - `M07_V03_AGENT_FINAL_ANSWER`
   - `M09_V03_TOOL_READ_TEXT_FILE`
   - `M10_EXCEL_SANDBOX_ANALYSIS` / `M10_V03_TOOL_ANALYZE_EXCEL_FILE`
4. 如果 Excel 失败，查看 `excel_analysis_runs` 的 `first_error`、`stderr`、`generated_code`、`final_code`。

## 非目标

- 不做日志搜索索引。
- 不做 token 成本统计。
- 不做审计报表。
- 不长期归档日志。
