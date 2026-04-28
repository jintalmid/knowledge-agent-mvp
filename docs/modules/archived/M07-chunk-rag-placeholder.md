# M07 Chunk / RAG 配置预留

## 模块目标

为阶段 0 提供最小 Chunk 生成能力，并为后续 Embedding、向量索引和 RAG 配置保留数据结构与 API 边界。

## 当前 Step 5 范围

- 新增 `document_chunks` 表，保存任务文件的文本 chunk 或 Excel 描述性 chunk
- 新增 `embedding_records` 表，仅预留向量记录结构，本阶段不写入真实向量
- 新增 `retrieval_settings` 配置存储，保存默认检索模式、chunk 参数和 top_k
- 文本文件基于解析后的 `parsed_contents.text_content` 按固定长度切片
- Excel / CSV 文件基于 `parsed_contents.excel_profile_json` 按 sheet 生成描述性 chunk

## 数据表

`document_chunks`

- `id`
- `task_file_id`
- `physical_file_id`
- `chunk_index`
- `content`
- `metadata_json`
- `created_at`

`embedding_records`

- `id`
- `chunk_id`
- `embedding_provider`
- `embedding_model`
- `vector_store`
- `vector_ref`
- `created_at`

## 对外接口

### POST /api/task-files/{task_file_id}/chunks

为已解析的任务文件生成或重新生成 chunk。重新生成时会删除该任务文件旧 chunk。

调用前置条件：

- `task_files.parse_status = parsed`
- `parsed_contents` 中存在对应记录

返回：

```json
[
  {
    "id": "chunk_xxx",
    "task_file_id": "tf_xxx",
    "physical_file_id": "pf_xxx",
    "chunk_index": 0,
    "content": "...",
    "metadata_json": {},
    "created_at": "..."
  }
]
```

### GET /api/task-files/{task_file_id}/chunks

按 `chunk_index ASC` 返回任务文件已生成的 chunk。

### GET /api/settings/retrieval

返回当前检索配置。

### PATCH /api/settings/retrieval

更新默认检索配置。当前支持字段：

- `retrieval_mode`: `summary_only` / `chunk_text` / `embedding` / `hybrid`
- `chunk_size`
- `chunk_overlap`
- `top_k`
- `embedding_provider`
- `embedding_model`
- `vector_store`

## 非目标

- 不生成真实 embedding
- 不接入向量数据库
- 不实现 rerank
- 不实现正式知识库 RAG

## 后续扩展

M09 / M10 / M11 可以读取 `document_chunks` 作为临时上下文来源。正式向量检索启用后，应写入 `embedding_records` 并由 `vector_ref` 指向外部向量存储。
