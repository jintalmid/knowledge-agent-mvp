# M06_LLM_SUMMARY_TAGGING LLM 摘要与标签

## 模块目标

基于 M05 的 `parsed_contents`，通过统一 LLM Service 生成文件摘要、关键词、标签和分类。

## 当前实现

- SQLite 表：`file_summaries`
- 前端页面：`/tasks/[taskId]/summaries`
- 统一调用：`app.services.llm.call_llm`
- 更新 `task_files.summary_status`
- 所有 LLM 调用由 M13 写入 `llm_call_logs`

## 数据字段

```text
id
task_file_id
physical_file_id
summary_text
keywords_json
tags_json
category
summary_method
llm_provider
llm_model
knowledge_item_id
created_at
updated_at
```

## API

```text
POST /api/task-files/{task_file_id}/summarize
POST /api/tasks/{task_id}/summarize-all
GET /api/tasks/{task_id}/summaries
GET /api/task-files/{task_file_id}/summary
```

## LLM 输出格式

文本文件要求 LLM 返回：

```json
{
  "summary": "...",
  "keywords": [],
  "tags": [],
  "category": "..."
}
```

CSV / Excel profile 要求 LLM 返回：

```json
{
  "summary": "...",
  "keywords": [],
  "tags": [],
  "category": "...",
  "table_understanding": {
    "main_subject": "...",
    "important_columns": [],
    "possible_questions": []
  }
}
```

## 错误策略

摘要必须调用 LLM。未配置 LLM、LLM 调用失败、LLM 返回非 JSON 或 JSON 缺少 `summary` 时，接口返回明确错误，并将 `summary_status` 标记为 `failed`。不做本地 fallback。

## 非目标

不实现本地摘要、Embedding、RAG、问答、知识库入库或多模型路由。
