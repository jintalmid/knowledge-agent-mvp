# M04 v0.3 LLM Service 与调用日志

## 模块目标

提供统一 LLM Service。所有摘要、工具、Agent plan、reflection、最终答案、Excel 代码生成都必须通过该服务调用模型，并写入 `llm_call_logs`。

## 当前实现

- Provider 类型：`openai_compatible`。
- 支持从 `.env` 读取 base URL、API key、model、timeout。
- 每次调用记录 prompt preview、response preview、状态、错误和耗时。
- 支持 `agent_run_id`、`iteration_id` 关联。
- 不做无 LLM fallback。

## 环境变量

- `LLM_PROVIDER_TYPE`
- `LLM_BASE_URL`
- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`

## 数据表

`llm_call_logs`：

- `id`
- `task_id`
- `agent_run_id`
- `iteration_id`
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

- `GET /api/settings/llm`
- `POST /api/settings/llm/test`
- `GET /api/llm-logs`
- `GET /api/llm-logs/{log_id}`

## 页面

- `/settings/llm`
- `/debug/llm-logs`

## 服务边界

其他模块不得直接用 HTTP client 调模型，必须调用 `services/llm.py`。

## 非目标

- 不实现多 Provider 管理 UI。
- 不实现模型路由策略。
- 不实现 token 计费统计。
