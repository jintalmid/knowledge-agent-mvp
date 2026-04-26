# M10 v0.3 analyze_excel_file 工具

## 模块目标

复用现有 Excel 代码生成与受限执行能力，将其包装为 Agent 可调用工具。

## 当前 Step 3 范围

- 通过 Tool Registry 注册 `analyze_excel_file`
- 通过 `POST /api/tools/analyze_excel_file/call` 调用
- 输入包含 `task_id`、`file_id`、`question`、`instruction`
- 复用已有 `parsed_contents.excel_profile_json`
- 复用已有 LLM 生成 Python 代码逻辑
- 复用已有静态安全检查和受限子进程执行逻辑
- 输出 `observation`、`result_json`、`generated_code`、`execution_status`
- `excel_analysis_runs` 支持可空 `agent_run_id` 和 `iteration_id`
- LLM 调用日志支持可空 `agent_run_id` 和 `iteration_id`

## 输入

```json
{
  "input": {
    "task_id": "task_xxx",
    "file_id": "tf_xxx",
    "question": "统计每个供应商销售额",
    "instruction": "返回总额最高的前三名",
    "sheet_name": "Sheet1",
    "agent_run_id": null,
    "iteration_id": null
  }
}
```

`file_id` 当前指 `task_files.id`。

## 输出

```json
{
  "tool_name": "analyze_excel_file",
  "status": "success",
  "output": {
    "task_id": "task_xxx",
    "file_id": "tf_xxx",
    "run_id": "excel_xxx",
    "agent_run_id": null,
    "iteration_id": null,
    "observation": "Excel analysis succeeded for 1.xlsx.",
    "result_json": {},
    "generated_code": "...",
    "final_code": "...",
    "execution_status": "success",
    "code_status": "passed",
    "repair_attempts": 0,
    "stdout": "",
    "stderr": "",
    "first_error": null
  }
}
```

## 数据来源

- `task_files`
- `physical_files`
- `parsed_contents.excel_profile_json`
- 原始上传文件
- `excel_analysis_runs`
- `llm_call_logs`

## 安全边界

继续沿用现有静态检查、临时目录执行、10 秒超时和最多 1 次修复。

## 非目标

- 不允许 Agent 直接执行任意 Python
- 不暴露任意本地文件路径
- 不实现 Docker 沙箱
