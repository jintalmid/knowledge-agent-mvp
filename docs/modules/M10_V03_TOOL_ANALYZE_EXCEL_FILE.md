# M10 v0.3 analyze_excel_file 工具

## 模块目标

将现有 Excel 分析能力封装为 Agent 工具。该工具使用 LLM 基于 Excel profile 生成 Python 分析代码，经过静态安全检查后在受限临时目录中执行，并输出结构化结果。

## 工具名

```text
analyze_excel_file
```

## 输入

```json
{
  "task_id": "task_xxx",
  "file_id": "tf_xxx",
  "question": "用户问题",
  "instruction": "分析指令",
  "sheet_name": "Sheet1",
  "agent_run_id": "arun_xxx",
  "iteration_id": "aiter_xxx"
}
```

`sheet_name`、`agent_run_id`、`iteration_id` 可为空。

## 输出

```json
{
  "observation": "...",
  "result_json": {},
  "generated_code": "...",
  "final_code": "...",
  "execution_status": "success|failed",
  "code_status": "passed|failed",
  "repair_attempts": 0,
  "stdout": "",
  "stderr": "",
  "first_error": null
}
```

## 数据表

`excel_analysis_runs`：

- `id`
- `task_id`
- `agent_run_id`
- `iteration_id`
- `task_file_id`
- `question_id`
- `generated_code`
- `final_code`
- `code_status`
- `execution_status`
- `result_json`
- `stdout`
- `stderr`
- `repair_attempts`
- `first_error`
- `created_at`
- `updated_at`

## 执行流程

1. 校验文件属于 task。
2. 校验文件已解析为 Excel profile。
3. 调用 LLM 生成 JSON：`analysis_plan`、`python_code`、`expected_output_schema`。
4. 如果 LLM 返回 JSON 不规范，调用一次 JSON 修复。
5. 静态安全检查 Python 代码。
6. 创建临时目录。
7. 将输入文件准备为 `input.xlsx`。
8. 执行 Python 子进程，timeout 10 秒。
9. 要求生成 `result.json`。
10. 如果执行失败，允许最多一次 LLM 自动修复代码。
11. 保存 `excel_analysis_runs`。
12. 成功时保存 Markdown answer。

## 静态安全检查

允许 imports：

- `pandas`
- `numpy`
- `json`
- `math`
- `statistics`

禁止：

- `os`
- `sys`
- `subprocess`
- `socket`
- `requests`
- `shutil`
- `pathlib`
- `eval`
- `exec`
- `__import__`
- `importlib`

`open()` 只允许写 `result.json`。支持安全常量形式：

```python
output_file = "result.json"
open(output_file, "w", encoding="utf-8")
```

## API

通过 M05：

- `POST /api/tools/analyze_excel_file/call`

兼容独立页面：

- `POST /api/task-files/{task_file_id}/excel/analyze`

## 页面

- `/tasks/{taskId}/excel`

## 非目标

- 不做 Docker 沙箱。
- 不允许任意文件读写。
- 不允许网络访问。
- 不做长时间计算任务。
