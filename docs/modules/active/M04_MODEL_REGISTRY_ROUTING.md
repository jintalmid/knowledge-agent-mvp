# M04 v0.3 模型管理与模型路由

## 模块目标

将简单 `.env` LLM 配置升级为独立模型模块，统一管理 Provider、模型能力标签和业务场景路由。所有 LLM 调用必须传入 `scenario`，由本模块解析最终调用的 `provider_id` 和 `model_id`。

## 当前实现

- Provider 管理：`model_providers`
- 模型管理：`model_configs`
- 场景路由：`model_route_configs`
- LLM 日志增强：`llm_call_logs.scenario`、`provider_id`、`model_id`
- 兼容 `.env`：启动/迁移时会把现有 `LLM_*` 配置种子化为 `default_text` 模型。
- 第一版仅执行 `openai_compatible` Provider；其他 Provider 类型只预留。

## 必需场景

`default_text` 是必需场景。若某个场景未配置专用模型，默认 fallback 到 `default_text`。如果 `default_text` 也不可用，LLM Service 必须明确报错，不做本地 fallback。

## 场景清单

- `default_text`
- `file_summary`
- `agent_planning`
- `agent_reflection`
- `final_answer`
- `text_tool`
- `excel_code_generation`
- `excel_code_repair`
- `excel_result_explanation`
- `document_parse_vision`
- `embedding_generation`
- `retrieval_rerank`
- `ppt_parse`
- `pdf_image_parse`
- `ocr`

多模态、embedding、reranker、OCR、PPT/PDF 图片解析当前只预留，不实现解析或向量能力。

## API

Provider：

- `GET /api/model-providers`
- `POST /api/model-providers`
- `GET /api/model-providers/{provider_id}`
- `PATCH /api/model-providers/{provider_id}`
- `DELETE /api/model-providers/{provider_id}`

Model：

- `GET /api/models`
- `POST /api/models`
- `GET /api/models/{model_id}`
- `PATCH /api/models/{model_id}`
- `DELETE /api/models/{model_id}`
- `POST /api/models/{model_id}/test`

Scenario / Route：

- `GET /api/model-scenarios`
- `GET /api/model-routes`
- `PATCH /api/model-routes/{scenario}`
- `POST /api/model-routes/{scenario}/test`

## 页面

- `/settings/models`
- `/settings/model-routing`
- `/debug/llm-logs`

## 调用边界

业务模块只传 `scenario`，不直接读取 `.env` 或选择模型：

- 文件摘要：`file_summary`
- Agent 规划：`agent_planning`
- Agent 自省：`agent_reflection`
- 最终答案：`final_answer`
- 文本工具：`text_tool`
- Excel 代码生成：`excel_code_generation`
- Excel 代码修复：`excel_code_repair`
- Excel 结果解释：`excel_result_explanation`

## 非目标

- 不实现 embedding。
- 不实现多模态文档解析。
- 不实现 Provider 插件系统。
- 不实现 API Key 加密存储；当前 MVP 使用 `api_key` 或 `api_key_env_name`。
