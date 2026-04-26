# M05 v0.3 Tool Registry Service

## 模块目标

提供 Agent 可调用工具的注册表和统一调用边界。阶段 0 工具调用不绕过 service 边界，所有需要 LLM 的工具都必须走统一 LLM Service。

## 当前 Step 3 范围

- 实现 `GET /api/tools`
- 实现 `POST /api/tools/{tool_name}/call`
- 注册 `list_file_summaries`
- 注册 `read_text_file`
- 注册 `analyze_excel_file`
- 工具调用统一返回 `tool_name`、`status`、`output`

## 工具契约

工具定义包含：

- `name`
- `description`
- `input_schema`
- `output_schema`
- `safety_notes`

## 已注册工具

- `list_file_summaries`
- `read_text_file`
- `analyze_excel_file`

## API

### GET /api/tools

返回所有已注册工具：

```json
[
  {
    "name": "read_text_file",
    "description": "...",
    "input_schema": {},
    "output_schema": {},
    "safety_notes": []
  }
]
```

### POST /api/tools/{tool_name}/call

请求：

```json
{
  "input": {}
}
```

响应：

```json
{
  "tool_name": "read_text_file",
  "status": "success",
  "output": {}
}
```

## 非目标

- 不允许任意 shell 工具
- 不允许网络访问工具
- 不实现插件市场
- 不实现 Agent Runner 循环
