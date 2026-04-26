# M08 v0.3 ReAct Iteration Loop

## 模块目标

定义 Agent 每轮的最小过程：`plan -> tool call -> observation -> reflection -> decision`。

## 当前 Step 4 范围

- 已实现最小 ReAct 循环
- 每轮先创建 `agent_iterations` 占位记录
- plan LLM 输出 JSON：
  - `thought`
  - `selected_file_ids`
  - `selected_tool`
  - `tool_instruction`
  - `reason`
  - `should_stop`
- 根据 `selected_tool` 调用 Tool Registry
- 将工具原始返回写入 `agent_iterations.tool_result_json`
- 将工具返回转换为 observation 并写入 `observations`
- reflection LLM 输出 JSON：
  - `reflection`
  - `is_enough`
  - `missing_information`
  - `next_step_hint`
  - `decision`
- `decision = stop` 时结束循环并生成最终答案

## 每轮数据映射

- `plan` 写入 `agent_iterations.plan_text`
- `tool call` 写入 `agent_iterations.tool_name` 和 `tool_input_json`
- `tool result` 写入 `agent_iterations.tool_result_json`
- `observation` 写入 `observations`
- `reflection` 写入 `agent_iterations.reflection_text`
- `decision` 写入 `agent_iterations.decision`

## decision 值

- `continue`
- `stop`

内部执行失败时，Agent Run 会标记为 `failed`，但单次工具失败会优先保存为 observation，交由 reflection 判断。

## 非目标

- 不实现 Tree-of-Thought
- 不实现多工具并行
- 不实现长期记忆
