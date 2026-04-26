# M09 v0.3 read_text_file 工具

## 模块目标

让 Agent 能读取已解析的文本类文件，并基于用户问题和工具指令抽取 observation 与 evidence。

## 当前实现

- 只读取属于指定 `task_id` 的 `task_file_id`。
- 只读取 `parsed_contents.content_type = text` 的文件。
- 支持 txt、md、pdf 解析后的文本内容。
- 调用 LLM 生成结构化 observation。
- LLM 调用会写入 `llm_call_logs`，并可关联 `agent_run_id` 和 `iteration_id`。

## 工具名

```text
read_text_file
```

## 输入

```json
{
  "task_id": "task_xxx",
  "file_id": "tf_xxx",
  "question": "用户问题",
  "instruction": "本次读取指令",
  "agent_run_id": "arun_xxx",
  "iteration_id": "aiter_xxx"
}
```

`agent_run_id` 和 `iteration_id` 可为空。

## 输出

```json
{
  "observation": "...",
  "evidence": ["..."],
  "confidence": "high|medium|low",
  "file": {},
  "llm_log_id": "llm_xxx"
}
```

## API 调用

通过 M05：

- `POST /api/tools/read_text_file/call`

## 安全边界

- 不读取任意本地路径。
- 不读取其他 task 的文件。
- 不读取原始上传文件，只读解析后的 `text_content`。

## 非目标

- 不做全文检索。
- 不做向量召回。
- 不做跨文件综合，跨文件综合由 Agent Runner 完成。
