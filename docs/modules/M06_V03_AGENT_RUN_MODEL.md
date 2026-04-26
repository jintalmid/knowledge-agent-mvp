# M06 v0.3 Agent Run 数据模型

## 模块目标

为 Agent Runner 提供可追踪的数据模型，使每次运行、每轮迭代和每个工具观察都能落库。

## 当前实现

新增三张核心表：

- `agent_runs`
- `agent_iterations`
- `observations`

并扩展：

- `answers.agent_run_id`
- `llm_call_logs.agent_run_id`
- `llm_call_logs.iteration_id`
- `excel_analysis_runs.agent_run_id`
- `excel_analysis_runs.iteration_id`

## agent_runs

字段：

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

字段：

- `id`
- `agent_run_id`
- `iteration_index`
- `plan_text`
- `tool_name`
- `tool_input_json`
- `tool_result_json`
- `reflection_text`
- `decision`
- `llm_call_log_id`
- `status`
- `error_message`
- `started_at`
- `completed_at`

## observations

字段：

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

## 关系

- 一个 task 可以有多个 Agent Run。
- 一个 Agent Run 有多轮 iteration。
- 一个 iteration 可以有多个 observation。
- 一个 answer 可以关联一个 Agent Run。
- LLM 日志可以关联 task、Agent Run 和 iteration。

## 非目标

- 不实现长期记忆。
- 不实现跨任务 Agent Run。
- 不实现异步队列状态机。
