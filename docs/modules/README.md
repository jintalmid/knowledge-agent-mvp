# Modules

当前项目唯一主线是 v0.3 AutoGPT / ReAct Agent Runner。`module-registry.json` 是前后端读取的模块注册表，且所有 `doc` 路径都必须指向 `active/`。

## 目录约定

- `active/`：当前唯一调用契约。后续开发、页面展示、API 对齐和 M12 能力盘点都只读取这里的 M00-M13 文档。
- `archived/`：历史文档。主要来自 v0.2 文档处理、检索和问答主线，只用于追溯，不作为当前模块边界。

## 当前模块

| 模块 | 名称 | 状态 | 文档 |
| --- | --- | --- | --- |
| M00 | 项目基座与配置 | implemented | [active/M00_V03_PROJECT_BASE.md](active/M00_V03_PROJECT_BASE.md) |
| M01 | 身份与权限预留 | reserved | [active/M01_V03_AUTH_PERMISSION_PLACEHOLDER.md](active/M01_V03_AUTH_PERMISSION_PLACEHOLDER.md) |
| M02 | Agent 任务空间 | implemented | [active/M02_V03_AGENT_WORKSPACE.md](active/M02_V03_AGENT_WORKSPACE.md) |
| M03 | 文件资产与解析支撑 | supporting | [active/M03_V03_FILE_CONTEXT_SUPPORT.md](active/M03_V03_FILE_CONTEXT_SUPPORT.md) |
| M04 | LLM Service 与调用日志 | implemented | [active/M04_V03_LLM_SERVICE_LOGGING.md](active/M04_V03_LLM_SERVICE_LOGGING.md) |
| M05 | Tool Registry Service | implemented | [active/M05_V03_TOOL_REGISTRY.md](active/M05_V03_TOOL_REGISTRY.md) |
| M06 | Agent Run 数据模型 | implemented | [active/M06_V03_AGENT_RUN_MODEL.md](active/M06_V03_AGENT_RUN_MODEL.md) |
| M07 | Agent Runner Service | implemented | [active/M07_V03_AGENT_RUNNER_SERVICE.md](active/M07_V03_AGENT_RUNNER_SERVICE.md) |
| M08 | ReAct Iteration Loop | implemented | [active/M08_V03_REACT_ITERATION_LOOP.md](active/M08_V03_REACT_ITERATION_LOOP.md) |
| M09 | read_text_file 工具 | implemented | [active/M09_V03_TOOL_READ_TEXT_FILE.md](active/M09_V03_TOOL_READ_TEXT_FILE.md) |
| M10 | analyze_excel_file 工具 | implemented | [active/M10_V03_TOOL_ANALYZE_EXCEL_FILE.md](active/M10_V03_TOOL_ANALYZE_EXCEL_FILE.md) |
| M11 | Agent Run 详情与结果展示 | implemented | [active/M11_V03_AGENT_RUN_VIEW.md](active/M11_V03_AGENT_RUN_VIEW.md) |
| M12 | v0.3 能力盘点 | planned | [active/M12_V03_AGENT_CAPABILITY_CHECK.md](active/M12_V03_AGENT_CAPABILITY_CHECK.md) |
| M13 | Debug 与历史日志 | implemented | [active/M13_V03_DEBUG_LOGS.md](active/M13_V03_DEBUG_LOGS.md) |

## 模块依赖

```text
M00 项目基座
  -> M01 默认身份上下文
  -> M02 Agent 任务空间
      -> M03 文件资产、自动解析、摘要上下文
      -> M04 LLM Service 与调用日志
      -> M06 Agent Run / Iteration / Observation 数据模型
      -> M05 Tool Registry
          -> M09 read_text_file
          -> M10 analyze_excel_file
      -> M07 Agent Runner
          -> M08 ReAct Iteration Loop
          -> M11 Agent Run 详情与最终结果
      -> M13 Debug 与历史日志
  -> M12 v0.3 能力盘点
```

M12 后续应以 `agent_runs`、`agent_iterations`、`observations`、`answers.agent_run_id`、`llm_call_logs.agent_run_id` / `iteration_id` 为核心检查对象。旧版 retrieval / text QA / phase0 检查可作为兼容页面和迁移参考，但不再定义当前主流程。
