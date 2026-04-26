# M09 文本问答与临时处理

## 模块目标

基于 M08 临时检索选出的文本文件，调用统一 LLM Service 生成 Markdown 答案，并保存问题、答案和来源引用。

## 当前 Step 6 范围

- 新增 `questions` 表保存用户问题
- 新增 `answers` 表保存 Markdown 答案、选中文件、来源引用、模型信息
- 实现任务级文本问答 API
- 所有问答 LLM 调用必须走统一 LLM Service，并写入 `llm_call_logs`
- 不做无 LLM fallback，LLM 未配置或调用失败时直接返回明确错误
- 仅处理已解析文本文件；Excel 分析留给 M10

## 数据表

`questions`

- `id`
- `task_id`
- `question_text`
- `question_type`
- `created_at`

`answers`

- `id`
- `task_id`
- `question_id`
- `answer_text_markdown`
- `selected_task_file_ids_json`
- `source_refs_json`
- `iteration_count`
- `llm_provider`
- `llm_model`
- `created_at`

## 对外接口

### POST /api/tasks/{task_id}/ask

请求：

```json
{
  "question_text": "问题文本"
}
```

处理流程：

1. 保存 `questions`
2. 调用 M08 `retrieve_task_files`
3. 过滤已解析的文本文件
4. 优先读取命中 chunk；没有 chunk 时读取 `parsed_contents.text_content`
5. 调用统一 LLM Service 生成 Markdown 答案
6. 保存 `answers`
7. 返回答案和来源

响应：

```json
{
  "id": "ans_xxx",
  "task_id": "task_xxx",
  "question_id": "q_xxx",
  "question_text": "问题文本",
  "question_type": "text_qa",
  "answer_text_markdown": "## 答案...",
  "selected_task_file_ids_json": ["tf_xxx"],
  "source_refs_json": [
    {
      "task_file_id": "tf_xxx",
      "physical_file_id": "pf_xxx",
      "display_name": "source.md",
      "score": 12,
      "matched_fields": ["chunk_content"],
      "reason": "命中 1 个 chunk，最高分 6",
      "content_type": "text",
      "chunk_refs": []
    }
  ],
  "iteration_count": 0,
  "llm_provider": "openai_compatible",
  "llm_model": "model-name",
  "created_at": "..."
}
```

### GET /api/tasks/{task_id}/results

返回任务下所有文本问答结果，按创建时间倒序。

### GET /api/answers/{answer_id}

返回单条答案详情。

## Prompt 约束

LLM 必须：

- 直接回答用户问题
- 标明依据哪些文件
- 不确定的内容必须说明
- 不编造未提供信息
- 输出 Markdown

## 前置条件

- 文件已完成 M05 解析
- 建议先完成 M06 摘要，以便 `summary_only` 检索能命中文件
- 若使用 `chunk_text`，需要先通过 M07 生成 chunk
- LLM 配置必须可用

## 非目标

- 不处理 Excel 代码分析
- 不实现多轮对话状态
- 不实现正式权限系统
- 不实现本地 fallback
