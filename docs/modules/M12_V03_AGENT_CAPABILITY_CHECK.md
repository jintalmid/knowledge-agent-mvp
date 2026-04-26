# M12 v0.3 Agent 能力盘点

## 模块目标

将 v0.2 的阶段 0 能力检查迁移为 Agent Runner 能力盘点。

## 当前 Step 1 范围

- 仅定义迁移方向
- 旧 `/modules/capability-check` 可暂时保留
- 尚未实现 Agent Runner 专属检查项

## 后续检查项建议

- `agent_run_created`
- `tool_registry_available`
- `read_text_file_available`
- `analyze_excel_file_available`
- `iteration_recorded`
- `observation_recorded`
- `final_answer_generated`
- `llm_logs_available`

## 非目标

- 不自动运行 Agent
- 不补齐缺失步骤
