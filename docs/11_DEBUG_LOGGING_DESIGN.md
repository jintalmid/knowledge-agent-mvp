# Debug Logging Design

## LLM 日志

所有 LLM 调用写入 `llm_call_logs`。

关键字段：

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

## 调试页面

`/debug/llm-logs` 支持：

- 查看任务、用户、团队、Agent Run、Iteration。
- 展开请求内容和响应内容。
- 按 `scenario`、`model_id`、`provider_id` 过滤。

## 设计原则

- 日志只记录 preview，不保存无限长度上下文。
- 日志必须能回答“哪个业务场景用了哪个模型”。
- v0.3 Agent Runner 调试应优先关联 `agent_run_id` 和 `iteration_id`。
