# M08 v0.3 ReAct Iteration Loop

## 模块目标

定义 Agent 每一轮的最小过程：`plan -> tool call -> observation -> reflection -> decision`。

## 当前实现

每轮执行顺序：

1. 创建 `agent_iterations` 占位记录。
2. LLM 生成 plan JSON。
3. Runner 根据 plan 构造工具输入。
4. 调用 Tool Registry。
5. 保存原始 tool result 到 `agent_iterations.tool_result_json`。
6. 将 tool result 转换为 observation 并写入 `observations`。
7. LLM 生成 reflection JSON。
8. 保存 reflection 和 decision。
9. 根据 decision 决定继续或停止。

## Plan JSON

```json
{
  "thought": "...",
  "selected_file_ids": ["..."],
  "selected_tool": "list_file_summaries|read_text_file|analyze_excel_file|none",
  "tool_instruction": "...",
  "reason": "...",
  "should_stop": false
}
```

## Reflection JSON

```json
{
  "reflection": "...",
  "is_enough": true,
  "missing_information": [],
  "next_step_hint": "...",
  "decision": "continue|stop"
}
```

## Decision

- `continue`: 进入下一轮。
- `stop`: 生成最终答案。

如果达到 `max_iterations`，Runner 会以 `max_iterations` 作为停止原因生成最终答案。

## 数据映射

- `plan` -> `agent_iterations.plan_text`
- `tool name` -> `agent_iterations.tool_name`
- `tool input` -> `agent_iterations.tool_input_json`
- `tool result` -> `agent_iterations.tool_result_json`
- `observation` -> `observations`
- `reflection` -> `agent_iterations.reflection_text`
- `decision` -> `agent_iterations.decision`

## 非目标

- 不实现 Tree-of-Thought。
- 不实现多工具并行。
- 不实现长期记忆检索。
