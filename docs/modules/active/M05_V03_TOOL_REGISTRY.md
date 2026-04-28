# M05 v0.3 Tool Registry Service

## 模块目标

提供 Agent 可调用工具的统一注册表和统一调用入口。Agent Runner 不直接依赖具体工具实现，而是通过 Tool Registry 调用工具。

## 当前实现

已注册工具：

- `list_file_summaries`
- `read_text_file`
- `analyze_excel_file`

## API

- `GET /api/tools`
- `POST /api/tools/{tool_name}/call`

请求格式：

```json
{
  "input": {}
}
```

响应格式：

```json
{
  "tool_name": "read_text_file",
  "status": "success",
  "output": {}
}
```

## 工具说明

`list_file_summaries`：

- 输入：`task_id`
- 输出：任务空间内已有摘要的文件列表。
- 不调用 LLM。

`read_text_file`：

- 输入：`task_id`、`file_id`、`question`、`instruction`、可选 `agent_run_id`、`iteration_id`
- 输出：`observation`、`evidence`、`confidence`。
- 调用 LLM，从 `parsed_contents.text_content` 中抽取证据。

`analyze_excel_file`：

- 输入：`task_id`、`file_id`、`question`、`instruction`、可选 `sheet_name`、`agent_run_id`、`iteration_id`
- 输出：`observation`、`result_json`、`generated_code`、`execution_status`。
- 复用 Excel 代码生成和受限执行能力。

## 服务边界

新增工具必须：

- 在 Tool Registry 中注册。
- 声明 input schema、output schema、safety notes。
- 返回统一 `ToolCallResponse`。
- 如调用 LLM，必须走 M04。

## 非目标

- 不做外部插件系统。
- 不做并行工具调用。
- 不做工具权限审批流。
