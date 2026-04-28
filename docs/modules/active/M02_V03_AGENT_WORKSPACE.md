# M02 v0.3 Agent 任务空间

## 模块目标

保留 v0.2 的 `tasks` 作为 Agent Run 的任务空间。任务空间用于承载文件上下文、问题、答案、Agent Run 和调试日志。

## 当前实现

任务支持创建、查看、更新和删除。删除任务时会级联删除任务文件、解析内容、摘要、结果和 Agent Run 相关记录。

## 数据表

`tasks` 字段：

- `id`
- `name`
- `description`
- `status`
- `owner_user_id`
- `department_id`
- `security_level`
- `knowledge_base_id`
- `template_id`
- `iteration_count`
- `created_at`
- `updated_at`

`knowledge_base_id` 和 `template_id` 当前仅预留。

## API

- `POST /api/tasks`
- `GET /api/tasks`
- `GET /api/tasks/{task_id}`
- `PATCH /api/tasks/{task_id}`
- `DELETE /api/tasks/{task_id}`

## 页面

- `/tasks`
- `/tasks/{taskId}`

任务详情页提供后续模块入口，包括文件、解析、摘要、Agent Run、结果和日志。

## 依赖

- M01 默认用户上下文。
- M00 SQLite 初始化。

## 非目标

- 不实现正式项目管理。
- 不实现多用户协作。
- 不实现知识库发布流程。
