# M10 Excel 分析与受限代码沙箱

## 模块目标

由 LLM 生成 Python 分析代码，经静态安全检查后在受限子进程中执行，并将结果保存为 Markdown 答案和 Excel 分析运行记录。

## 当前 Step 7 范围

- 新增 `excel_analysis_runs` 表
- 实现 Excel 分析 API
- 调用统一 LLM Service 生成分析代码
- 对生成代码做静态安全检查
- 在临时目录中执行代码，固定输入 `input.xlsx`，固定输出 `result.json`
- 执行失败后最多调用 LLM 自动修复一次
- 成功后生成 Markdown 结果并保存到 `answers`
- 前端页面 `/tasks/[taskId]/excel` 展示分析结果、代码、stdout、stderr、修复次数

## 数据表

`excel_analysis_runs`

- `id`
- `task_id`
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

## 对外接口

### POST /api/task-files/{task_file_id}/excel/analyze

请求：

```json
{
  "question": "统计各部门销售额，并找出最高的前三项",
  "sheet_name": "Sheet1"
}
```

响应：

```json
{
  "run": {
    "id": "excel_xxx",
    "task_id": "task_xxx",
    "task_file_id": "tf_xxx",
    "question_id": "q_xxx",
    "generated_code": "...",
    "final_code": "...",
    "code_status": "passed",
    "execution_status": "success",
    "result_json": {},
    "stdout": "",
    "stderr": "",
    "repair_attempts": 0,
    "first_error": null,
    "created_at": "...",
    "updated_at": "..."
  },
  "answer": {
    "id": "ans_xxx",
    "answer_text_markdown": "## Excel 分析结果..."
  }
}
```

失败时仍返回 `run`，`execution_status = failed`，`answer = null`。

## 执行流程

1. 校验 `task_file` 存在且已解析为 `content_type = excel`
2. 读取 `parsed_contents.excel_profile_json`
3. 保存 `questions`
4. 调用 LLM 返回：

```json
{
  "analysis_plan": "...",
  "python_code": "...",
  "expected_output_schema": {}
}
```

5. 静态安全检查 `python_code`
6. 创建临时目录
7. 将源文件转换或复制为 `input.xlsx`
8. 执行 Python 代码，要求生成 `result.json`
9. 如果失败，调用 LLM 修复一次并重新执行
10. 保存 `excel_analysis_runs`
11. 成功时生成 Markdown 并保存 `answers`

## 静态安全检查

禁止：

- `import os`
- `import sys`
- `subprocess`
- `socket`
- `requests`
- `shutil`
- `pathlib`
- `eval(`
- `exec(`
- `__import__`
- `importlib`

允许 import：

- `pandas`
- `numpy`
- `json`
- `math`
- `statistics`

`open()` 仅允许写入 `result.json`。

## 执行限制

- `timeout = 10` 秒
- 工作目录为临时目录
- 输入文件名固定为 `input.xlsx`
- 输出文件名固定为 `result.json`
- 捕获 `stdout` / `stderr`

## 非目标

- 不实现 Docker 沙箱
- 不实现多 Agent 编排
- 不允许网络访问类库
- 不实现本地无 LLM fallback
