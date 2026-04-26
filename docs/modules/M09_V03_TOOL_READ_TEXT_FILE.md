# M09 v0.3 read_text_file 工具

## 模块目标

为 Agent 提供受控文本读取能力：从任务空间中读取已解析文本文件，并调用 LLM 抽取面向问题的 `observation` 和 `evidence`。

## 当前 Step 2 范围

- 通过 Tool Registry 注册 `read_text_file`
- 通过 `POST /api/tools/read_text_file/call` 调用
- 输入包含 `task_id`、`file_id`、`question`、`instruction`
- 只读取 `parsed_contents.content_type = text` 的内容
- LLM 返回结构化 `observation`、`evidence`、`confidence`
- LLM 调用写入 `llm_call_logs`

## 输入

```json
{
  "input": {
    "task_id": "task_xxx",
    "file_id": "tf_xxx",
    "question": "用户问题",
    "instruction": "请抽取与问题相关的依据"
  }
}
```

`file_id` 当前指 `task_files.id`。

## 输出

```json
{
  "tool_name": "read_text_file",
  "status": "success",
  "output": {
    "task_id": "task_xxx",
    "file_id": "tf_xxx",
    "file": {
      "task_file_id": "tf_xxx",
      "physical_file_id": "pf_xxx",
      "display_name": "source.txt",
      "parse_quality": "ok"
    },
    "observation": "...",
    "evidence": ["..."],
    "confidence": "high",
    "llm_log_id": "llm_xxx"
  }
}
```

## LLM Prompt 约束

LLM 必须：

- 只基于已提供的 parsed text
- 不编造文件中不存在的信息
- 信息不足时在 `observation` 中说明
- 返回 JSON，不返回 Markdown

## 数据来源

- `task_files`
- `parsed_contents.text_content`
- `llm_call_logs`

## 非目标

- 不读取任意本地路径
- 不绕过任务文件引用
- 不实现 Agent Runner 循环
