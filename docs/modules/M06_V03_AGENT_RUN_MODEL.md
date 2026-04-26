# M06 v0.3 Agent Run 数据模型

## 模块目标

新增 Agent Runner 阶段 0 所需的三张核心表：`agent_runs`、`agent_iterations`、`observations`。

## 当前 Step 1 范围

已新增数据表，但尚未实现 Runner API 或页面。

## agent_runs

- `id`
- `task_id`
- `goal`
- `status`
- `max_iterations`
- `current_iteration`
- `final_answer_markdown`
- `stop_reason`
- `owner_user_id`
- `department_id`
- `security_level`
- `created_at`
- `updated_at`

## agent_iterations

- `id`
- `agent_run_id`
- `iteration_index`
- `plan_text`
- `tool_name`
- `tool_input_json`
- `reflection_text`
- `decision`
- `llm_call_log_id`
- `status`
- `error_message`
- `started_at`
- `completed_at`

## observations

- `id`
- `agent_run_id`
- `agent_iteration_id`
- `tool_name`
- `observation_type`
- `content_text`
- `content_json`
- `status`
- `error_message`
- `created_at`

## 关联现有表

`answers` 已支持：

- `agent_run_id`

用于把 Agent 最终答案关联回某次 Agent Run。非 Agent 旧问答结果可以为空。

`llm_call_logs` 已支持：

- `agent_run_id`
- `iteration_id`

用于把每轮 plan、reflection、decision、final answer 的 LLM 调用和 Agent Run / Iteration 对齐。非 Agent 旧调用日志可以为空。

## 后续调用约定

Agent Runner 每轮必须先写 `agent_iterations`，工具执行结果必须写 `observations`。
