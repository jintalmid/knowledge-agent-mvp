# M07 v0.3 Agent Runner Service

## 模块目标

实现 Agent Run 主循环，从用户目标开始，最多执行 10 轮 ReAct 迭代，并生成最终答案。

## 当前 Step 4 范围

- 已实现 `POST /api/tasks/{task_id}/agent-runs`
- 请求输入 `question` 和 `max_iterations`
- 创建 `questions` 记录
- 创建 `agent_runs` 记录
- 按最多 10 轮执行 Agent Runner 主循环
- 每轮读取用户问题、文件摘要、历史 observations 和可用工具列表
- 每轮调用 LLM 生成 plan JSON
- 根据 plan 调用 Tool Registry
- 保存 tool result、observation 和 reflection
- 停止或达到轮数上限后调用 LLM 生成最终 Markdown 答案
- 最终答案写入 `answers`，并通过 `answers.agent_run_id` 关联 Agent Run

## API

### `POST /api/tasks/{task_id}/agent-runs`

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
  "iteration_count": 1
}
```

## 执行约束

- 默认 `max_iterations = 10`
- `max_iterations` 当前限制为 1 到 10
- 所有 LLM 调用走 M04
- 所有工具调用走 M05
- 每轮过程写入 M06 数据表
- 工具调用失败会写入 observation，Runner 再交给 reflection 决定是否继续

## 非目标

- 不做多 Agent 编排
- 不做后台队列
- 不做并发工具执行
- 不实现 Agent Run 详情页，详情页属于 M11 后续步骤
