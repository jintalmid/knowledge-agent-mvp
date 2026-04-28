# M04_TASK_FILE_REFERENCE 任务文件引用

## 模块目标

维护任务空间内的文件引用，让任务文件与物理文件资产解耦。一个 `physical_file` 可以被多个 `task_file` 引用。

## 当前实现

- SQLite 表：`task_files`
- 上传 API 先校验 `task_id`
- 计算文件 SHA256
- 根据 `content_hash` 查找或创建 `physical_file`
- 创建 `task_file` 引用
- 更新 `physical_files.ref_count`
- 前端页面：`/tasks/[taskId]/files`

## 数据字段

```text
id
task_id
physical_file_id
display_name
file_role
parse_status
summary_status
embedding_status
owner_user_id
department_id
security_level
created_at
updated_at
```

## API

```text
POST /api/tasks/{task_id}/files
GET /api/tasks/{task_id}/files
GET /api/task-files/{task_file_id}
DELETE /api/task-files/{task_file_id}
```

## 默认状态

```text
file_role = source
parse_status = not_started
summary_status = not_started
embedding_status = not_started
```

身份字段由 M01 默认身份上下文注入。

## 删除策略

删除 `task_file` 时只删除任务引用，并将对应 `physical_file.ref_count - 1`。当 `ref_count = 0` 时，物理文件暂不删除。

## 非目标

不实现文件解析、摘要、Embedding、RAG、下载、预览或正式知识库入库。

## 调用边界

后续 M05 文件解析应读取 `task_file` 与 `physical_file` 的关联信息，不应重新处理上传和去重逻辑。
