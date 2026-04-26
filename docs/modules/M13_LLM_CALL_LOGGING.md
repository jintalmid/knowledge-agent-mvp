# M13_LLM_CALL_LOGGING LLM 调用日志与 Debug

## 模块目标

为所有 LLM 调用提供统一日志记录和 Debug 查询能力。

## 当前实现

- SQLite 表：`llm_call_logs`
- 统一 LLM Service：`app.services.llm`
- 当前 Provider：`openai_compatible`
- 设置页面：`/settings/llm`
- 日志页面：`/debug/llm-logs`

## 配置

从 `backend/.env` 读取：

```text
LLM_PROVIDER_TYPE=openai_compatible
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
```

## 数据字段

```text
id
task_id
module_name
provider_type
model_name
prompt_preview
response_preview
status
error_message
latency_ms
created_at
```

## API

```text
GET /api/settings/llm
POST /api/settings/llm/test
GET /api/llm-logs
GET /api/llm-logs/{log_id}
```

## 调用约束

所有 LLM 调用必须通过统一 LLM Service。服务会记录成功和失败调用，包括未配置 LLM 时的失败日志。

## 非目标

不实现多 Provider、密钥管理 UI、流式输出、费用统计、prompt 模板管理或本地模型 fallback。
