# M04 v0.3 LLM Service 与调用日志

## 模块目标

保留统一 LLM Service、OpenAI-compatible Adapter 和 LLM 调用日志。Agent Runner、工具代码生成、反思和最终答案生成都必须走该服务。

## 当前 Step 1 范围

- 保留 `.env` 中 LLM 配置
- 保留 `llm_call_logs`
- `llm_call_logs` 支持可空关联字段 `agent_run_id` 和 `iteration_id`
- 保留 `/settings/llm`
- 保留 `/debug/llm-logs`

## 后续调用约定

Agent Runner 每次 plan、reflection、final answer 都必须记录 `llm_call_logs.module_name`，建议使用：

- `M07_AGENT_RUNNER_SERVICE`
- `M08_REACT_ITERATION_LOOP`
- `M10_TOOL_ANALYZE_EXCEL_FILE`

Agent Runner 调用 LLM 时应传入：

- `agent_run_id`
- `iteration_id`

非 Agent 场景可以继续为空，以兼容现有摘要、问答和 Excel 分析能力。

## 非目标

- 不增加本地 fallback
- 不新增非 OpenAI-compatible Provider
