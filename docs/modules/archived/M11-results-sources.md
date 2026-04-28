# M11 结果与来源展示

## 模块目标

展示系统输出结果、来源文件、引用依据和历史记录。Step 7 已覆盖文本问答结果和 Excel 分析结果。

## 当前 Step 7 范围

- 前端页面 `/tasks/[taskId]/ask`：输入问题、生成 Markdown 答案、展示来源、一键复制 Markdown
- 前端页面 `/tasks/[taskId]/excel`：选择 Excel 文件和 sheet，展示分析 Markdown、生成代码、最终代码、stdout、stderr、修复次数
- 前端页面 `/tasks/[taskId]/results`：查看历史问答结果、切换结果、复制 Markdown、查看来源文件
- 后端复用 M09 / M10 写入的 `answers` 和 `source_refs_json`

## 对外接口

M11 结果展示读取以下接口：

- `GET /api/tasks/{task_id}/results`
- `GET /api/answers/{answer_id}`
- `POST /api/task-files/{task_file_id}/excel/analyze`

返回结构由 M09 `AnswerRead` 定义，核心字段：

- `answer_text_markdown`
- `question_text`
- `selected_task_file_ids_json`
- `source_refs_json`
- `llm_provider`
- `llm_model`
- `created_at`

## 来源展示

`source_refs_json` 中每个来源包含：

- `task_file_id`
- `physical_file_id`
- `display_name`
- `score`
- `matched_fields`
- `reason`
- `content_type`
- `chunk_refs`

## 非目标

- 不实现引用高亮定位
- 不实现正式知识库结果页
- 不展示完整 LLM 日志详情，LLM 日志仍由 M13 提供

## 后续扩展

后续可为 `excel_analysis_runs` 增加独立详情页，并在结果页中展开代码执行日志、产物下载和引用定位。
