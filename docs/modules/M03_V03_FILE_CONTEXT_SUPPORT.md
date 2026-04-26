# M03 v0.3 文件资产与解析支撑

## 模块目标

保留文件上传、物理文件资产、任务文件引用、基础解析和摘要上下文，为 Agent 工具提供可读取的文件基础数据。

## 当前实现

- 文件上传保存到 `backend/uploads/{sha256}/`。
- 物理文件基于 SHA256 去重。
- `physical_files` 和 `task_files` 解耦。
- 支持 txt、md、pdf、csv、xlsx、xls。
- 上传创建 task_file 后自动调用解析服务。
- 自动解析失败不会导致上传接口失败；文件保留，`parse_status = failed`，`parse_error` 记录简短错误。
- 文本/PDF 解析为 `text_content`。
- CSV/Excel 解析为 `excel_profile_json`。
- 文件摘要保存到 `file_summaries`。

## 数据表

`physical_files`：

- `id`
- `content_hash`
- `original_filename`
- `file_ext`
- `mime_type`
- `file_size`
- `storage_path`
- `ref_count`
- `created_at`
- `updated_at`

`task_files`：

- `id`
- `task_id`
- `physical_file_id`
- `display_name`
- `file_role`
- `parse_status`
- `parse_error`
- `summary_status`
- `embedding_status`
- `owner_user_id`
- `department_id`
- `security_level`
- `created_at`
- `updated_at`

`parsed_contents`：

- `id`
- `task_file_id`
- `physical_file_id`
- `content_type`
- `text_content`
- `excel_profile_json`
- `parse_quality`
- `created_at`
- `updated_at`

## API

文件：

- `POST /api/tasks/{task_id}/files`
- `GET /api/tasks/{task_id}/files`
- `GET /api/task-files/{task_file_id}`
- `DELETE /api/task-files/{task_file_id}`
- `GET /api/physical-files/{physical_file_id}`

解析：

- `POST /api/task-files/{task_file_id}/parse`
- `POST /api/tasks/{task_id}/parse-all`
- `GET /api/task-files/{task_file_id}/parsed-content`

摘要：

- `POST /api/task-files/{task_file_id}/summarize`
- `POST /api/tasks/{task_id}/summarize-all`
- `GET /api/tasks/{task_id}/summaries`
- `GET /api/task-files/{task_file_id}/summary`

## 页面

- `/tasks/{taskId}/files`
- `/tasks/{taskId}/parsing`
- `/tasks/{taskId}/summaries`

普通主流程从 `/tasks/{taskId}/files` 上传后即可使用文件。`/tasks/{taskId}/parsing` 保留为高级页面，用于 Debug、批量重试、查看文本预览和 Excel profile。

## 降级说明

复杂去重策略、清理任务、正式知识库资产生命周期在 v0.3 中降级为未来预留。

## 非目标

- 不做文件版本管理。
- 不做远程对象存储。
- 不做权限级文件隔离。
