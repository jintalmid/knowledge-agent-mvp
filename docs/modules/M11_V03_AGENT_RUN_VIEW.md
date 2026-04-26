# M11 v0.3 Agent Run 详情与结果展示

## 模块目标

展示 Agent Run 的目标、状态、每轮计划、工具调用、观察、反思、决策和最终答案，并在结果页展示 Markdown 答案、来源文件和不确定性。

## 当前实现

页面：

- `/tasks/{taskId}/agent`
- `/tasks/{taskId}/runs/{runId}`
- `/tasks/{taskId}/results`

API：

- `GET /api/agent-runs/{run_id}`
- `GET /api/tasks/{task_id}/results`
- `GET /api/answers/{answer_id}`

## Agent 启动页

`/tasks/{taskId}/agent` 提供：

- 问题输入。
- `max_iterations` 设置，默认 10。
- 启动 Agent Run。
- 成功后跳转到 `/tasks/{taskId}/runs/{runId}`。

## Agent Run 详情页

`/tasks/{taskId}/runs/{runId}` 展示：

- run status。
- 当前轮数和最大轮数。
- stop reason。
- 用户问题。
- 每轮 thought。
- selected files。
- selected tool。
- instruction。
- observation。
- tool result JSON。
- reflection。
- missing information。
- next step hint。
- decision。
- final answer。

## 结果页

`/tasks/{taskId}/results` 展示：

- 历史答案。
- 最终 Markdown 答案。
- used files。
- uncertainties。
- LLM provider/model。
- Agent Run 详情链接。
- 复制 Markdown。
- 重新运行。

## 复制 Markdown

前端使用 `frontend/lib/clipboard.ts`。当浏览器拒绝 `navigator.clipboard.writeText()` 时，会自动尝试 textarea fallback。

## 非目标

- 不实现实时流式输出。
- 不实现运行中增量刷新。
- 不实现可视化 DAG。
