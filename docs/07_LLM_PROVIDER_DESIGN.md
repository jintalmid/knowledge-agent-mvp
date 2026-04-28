# LLM Provider Design

当前 v0.3 使用模型注册与路由模块管理 LLM。

## Provider

`model_providers` 保存 Provider 连接信息：

- `provider_type`：当前仅实现 `openai_compatible`。
- `base_url`：OpenAI-compatible API 根地址。
- `api_key_env_name`：推荐方式，例如 `LLM_API_KEY`。
- `api_key`：MVP 可用的直接保存方式，后续应替换为加密存储。

## Model

`model_configs` 保存模型配置：

- `model_name` 是真实 API 调用时传给 Provider 的模型名。
- `model_types_json` 表示模型类型，如 `text`、`vision`、`embedding`。
- `capability_tags_json` 表示能力标签，如 `reasoning`、`code`、`ocr`。
- `context_window` 表示模型可接收的上下文窗口。
- `output_window` 表示模型建议或允许的最大输出窗口。
- `is_default_text_model` 标识默认纯文本大语言模型。

前端 `/settings/models` 以 Provider 为父级展示模型；新增模型只能在某个 Provider 下发起。模型类型和能力标签使用按钮式多选，避免通过逗号文本维护结构化能力。

## Routing

业务代码调用 LLM Service 时只传 `scenario`。LLM Service 按以下顺序解析：

1. 查找 `model_route_configs.scenario` 对应的专用模型。
2. 如果没有，沿 `fallback_scenario` 查找。
3. 如果仍没有，使用 `is_default_text_model = true` 的模型。
4. 如果 default_text 不存在或不可用，返回明确错误。

## 当前场景

核心已使用：

- `file_summary`
- `agent_planning`
- `agent_reflection`
- `final_answer`
- `text_tool`
- `excel_code_generation`
- `excel_code_repair`

预留能力：

- `document_parse_vision`
- `embedding_generation`
- `retrieval_rerank`
- `ppt_parse`
- `pdf_image_parse`
- `ocr`

## 兼容策略

为了兼容已有部署，数据库初始化时会把 `backend/.env` 中的 `LLM_PROVIDER_TYPE`、`LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL` 种子化为默认 Provider 和 default_text 模型。

`scripts/test_llm_env.sh` 只用于验证 `.env` 和网络连通性，不读取数据库中的 Provider、模型配置或路由。日常模型测试应使用 `/settings/models`，业务场景测试应使用 `/settings/model-routing`。
