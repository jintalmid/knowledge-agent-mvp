# M07 v0.3 Agent Runner Service

## 模块目标

执行 Agent Run 主循环，从用户问题出发，最多运行 10 轮 ReAct 迭代，并生成最终 Markdown 答案。

## 当前实现

- `POST /api/tasks/{task_id}/agent-runs`
- 创建 `questions`。
- 创建 `agent_runs`。
- 每轮创建 `agent_iterations`。
- 每轮读取用户问题、文件摘要、历史 observations/reflections、可用工具列表。
- 调用 LLM 生成 plan JSON。
- 根据 plan 调用 Tool Registry。
- 保存 tool result 和 observation。
- 调用 LLM 生成 reflection JSON。
- 根据 decision 判断继续或停止。
- 停止或达到 `max_iterations` 后调用 LLM 生成最终答案。
- 最终答案写入 `answers` 和 `agent_runs.final_answer_markdown`。

## API

`POST /api/tasks/{task_id}/agent-runs`

请求：

```json
{
  "question": "用户问题",
  "max_iterations": 10
}
```

响应：

```json
{
  "agent_run_id": "arun_xxx",
  "answer_id": "ans_xxx",
  "status": "completed",
  "iteration_count": 2
}
```

`GET /api/agent-runs/{run_id}` 返回运行详情。

## Runner 保护逻辑

- `max_iterations` 限制为 1 到 10。
- 同一工具 + 同一文件失败后，避免盲目重复调用。
- 当 planner 误用 `read_text_file` 读取 Excel 文件时，会自动纠偏为 `analyze_excel_file`。
- 当 planner 误用 `analyze_excel_file` 读取文本/PDF 时，会自动纠偏为 `read_text_file`。
- 对达标/不达标/目标类问题，会提示模型同时检查目标文件和实际指标文件。

## 依赖

- M04 LLM Service。
- M05 Tool Registry。
- M06 Agent Run 数据模型。
- M08 ReAct 迭代结构。

## 非目标

- 不做后台队列。
- 不做实时流式输出。
- 不做多 Agent 编排。
- 不做并行工具调用。
