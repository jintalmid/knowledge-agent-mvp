# M11 v0.3 Agent Run 详情与结果展示

## 模块目标

展示 Agent Run 的目标、状态、每轮计划、工具调用、观察、反思、决策和最终答案。

## 当前 Step 5 范围

- 已实现 Agent Run 启动页
- 已实现 Agent Run 详情页
- 已增强任务结果页，使 Agent 最终答案可以查看来源、缺失/不确定性提示，并复制 Markdown

## 页面

- `/tasks/{task_id}/agent`
- `/tasks/{task_id}/runs/{run_id}`
- `/tasks/{task_id}/results`

## 展示内容

- Agent Run 基本信息
- 每轮 `thought`
- 每轮 `selected_file_ids`
- 每轮 `selected_tool`
- 每轮 `tool_instruction`
- 每轮 observation
- 每轮 reflection
- 每轮 decision
- 最终答案 Markdown
- used files
- uncertainties

最终答案应优先读取 `agent_runs.final_answer_markdown`，并可通过 `answers.agent_run_id` 找到保存到历史结果中的答案记录。

## 非目标

- 不替代现有文件页面
- 不实现实时流式更新
