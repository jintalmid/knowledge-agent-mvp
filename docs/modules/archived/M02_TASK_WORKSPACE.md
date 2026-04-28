# M02_TASK_WORKSPACE 任务空间

## 模块目标

提供阶段 0 的临时任务空间，用于后续文件引用、解析、摘要、检索、问答和 Excel 分析挂载。

## 当前实现

- SQLite 表：`tasks`
- 后端 REST API：任务 CRUD
- 前端页面：`/tasks`、`/tasks/[taskId]`
- 任务详情页展示后续模块入口，入口状态为“未实现”

## 数据字段

```text
id
name
description
status
owner_user_id
department_id
security_level
knowledge_base_id
template_id
iteration_count
created_at
updated_at
```

## API

```text
POST /api/tasks
GET /api/tasks
GET /api/tasks/{task_id}
PATCH /api/tasks/{task_id}
DELETE /api/tasks/{task_id}
```

## 默认行为

- 新建任务默认状态为 `draft`
- 新建任务默认 `iteration_count = 0`
- 身份字段由 M01 默认身份上下文注入

## 非目标

不实现文件上传、任务文件引用、文件解析、LLM 摘要、问答、Excel 分析、RAG 或正式知识库。

## 扩展预留

- `knowledge_base_id` 为后续正式知识库预留
- `template_id` 为后续模板管理预留
- `iteration_count` 为后续任务多轮处理和自动修复流程预留
