# M02 v0.3 Agent 任务空间

## 模块目标

保留现有 `tasks` 表和任务页面，把它作为 Agent Run 的 workspace。任务空间仍承载上传文件、解析内容、摘要、Excel profile 和未来 Agent Run。

## 当前 Step 1 范围

- 不修改现有任务 CRUD
- `knowledge_base_id`、`template_id` 降级为未来预留字段
- 新增 `agent_runs.task_id` 可关联现有任务

## 后续调用约定

Agent Runner 默认在某个 `task_id` 下执行，并通过工具读取该任务空间中的文件和解析内容。

## 非目标

- 不实现正式知识库
- 不实现模板管理
