# M08 临时检索与文件筛选

## 模块目标

在任务空间内根据用户问题筛选相关文件，为 M09 文本问答和 M10 Excel 分析选择候选文件。

## 当前 Step 5 范围

- 实现 `summary_only` 检索：基于 `file_summaries` 的摘要、关键词、标签、分类和文件名匹配
- 实现 `chunk_text` 检索：基于 `document_chunks.content` 和文件名匹配
- `embedding` 与 `hybrid` 返回“已预留，未启用”状态，不抛出 500
- 前端页面 `/tasks/[taskId]/retrieval` 支持输入问题、选择检索模式、展示候选文件和匹配原因

## 对外接口

### POST /api/tasks/{task_id}/retrieve

请求：

```json
{
  "question": "用户问题",
  "retrieval_mode": "summary_only",
  "top_k": 5
}
```

`retrieval_mode` 可选。未传时使用 `/api/settings/retrieval` 中的默认配置。

响应：

```json
{
  "retrieval_mode": "summary_only",
  "status": "ok",
  "message": "基于文件摘要、关键词、标签和分类进行轻量匹配。",
  "results": [
    {
      "task_file_id": "tf_xxx",
      "physical_file_id": "pf_xxx",
      "display_name": "source.txt",
      "score": 12,
      "matched_fields": ["summary_text", "keywords_tags"],
      "reason": "命中摘要/标签字段：summary_text, keywords_tags",
      "chunk_matches": []
    }
  ]
}
```

`chunk_text` 模式下，`chunk_matches` 会包含命中的 chunk 预览：

```json
{
  "chunk_id": "chunk_xxx",
  "chunk_index": 0,
  "score": 6,
  "preview": "..."
}
```

`embedding` 和 `hybrid` 响应：

```json
{
  "retrieval_mode": "embedding",
  "status": "reserved",
  "message": "embedding 已预留，阶段 0 未启用向量检索。",
  "results": []
}
```

## 检索规则

阶段 0 使用轻量关键词匹配：

- 英文、数字按词匹配
- 中文按单字粗粒度匹配
- 文件名、摘要、分类、关键词、标签、chunk 内容使用不同权重计分
- 仅返回得分大于 0 的候选文件

## 前置条件

- `summary_only` 需要先完成 M06 摘要
- `chunk_text` 需要先完成 M05 解析，并调用 M07 chunk 生成接口

## 非目标

- 不调用 LLM 做文件筛选
- 不实现 embedding 检索
- 不实现 hybrid 检索
- 不实现正式知识库权限过滤

## 后续扩展

M09 / M10 应优先调用本模块获得候选文件，再根据候选文件类型分别进入文本问答或 Excel 分析。
