# M03 v0.3 文件资产与解析支撑

## 模块目标

保留 v0.2 中已实现的文件上传、基础解析和摘要能力，作为 Agent 工具的上下文来源。

## 当前 Step 1 范围

- 保留 `physical_files`
- 保留 `task_files`
- 保留 `parsed_contents`
- 保留 `file_summaries`
- 保留上传、解析、摘要 API 和页面
- SHA256 去重复杂逻辑降级为支撑能力，不再是项目主线

## 后续调用约定

`read_text_file` 工具应优先读取 `parsed_contents.text_content`。`analyze_excel_file` 工具应读取 `parsed_contents.excel_profile_json` 和原始上传文件。

## 非目标

- 不扩展正式知识库
- 不实现 RAG 索引
- 不扩展文件权限系统
