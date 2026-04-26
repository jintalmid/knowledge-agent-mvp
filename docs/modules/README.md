# Modules

当前模块以 v0.3 Agent Runner 主线为准。`module-registry.json` 是前后端读取的模块注册表，本目录中的 v0.3 文档是各模块的调用契约。

## 当前模块

| 模块 | 名称 | 状态 | 文档 |
| --- | --- | --- | --- |
| M00 | 项目基座与配置 | implemented | [M00_V03_PROJECT_BASE.md](M00_V03_PROJECT_BASE.md) |
| M01 | 身份与权限预留 | reserved | [M01_V03_AUTH_PERMISSION_PLACEHOLDER.md](M01_V03_AUTH_PERMISSION_PLACEHOLDER.md) |
| M02 | Agent 任务空间 | implemented | [M02_V03_AGENT_WORKSPACE.md](M02_V03_AGENT_WORKSPACE.md) |
| M03 | 文件资产与解析支撑 | supporting | [M03_V03_FILE_CONTEXT_SUPPORT.md](M03_V03_FILE_CONTEXT_SUPPORT.md) |
| M04 | LLM Service 与调用日志 | implemented | [M04_V03_LLM_SERVICE_LOGGING.md](M04_V03_LLM_SERVICE_LOGGING.md) |
| M05 | Tool Registry Service | implemented | [M05_V03_TOOL_REGISTRY.md](M05_V03_TOOL_REGISTRY.md) |
| M06 | Agent Run 数据模型 | implemented | [M06_V03_AGENT_RUN_MODEL.md](M06_V03_AGENT_RUN_MODEL.md) |
| M07 | Agent Runner Service | implemented | [M07_V03_AGENT_RUNNER_SERVICE.md](M07_V03_AGENT_RUNNER_SERVICE.md) |
| M08 | ReAct Iteration Loop | implemented | [M08_V03_REACT_ITERATION_LOOP.md](M08_V03_REACT_ITERATION_LOOP.md) |
| M09 | read_text_file 工具 | implemented | [M09_V03_TOOL_READ_TEXT_FILE.md](M09_V03_TOOL_READ_TEXT_FILE.md) |
| M10 | analyze_excel_file 工具 | implemented | [M10_V03_TOOL_ANALYZE_EXCEL_FILE.md](M10_V03_TOOL_ANALYZE_EXCEL_FILE.md) |
| M11 | Agent Run 详情与结果展示 | implemented | [M11_V03_AGENT_RUN_VIEW.md](M11_V03_AGENT_RUN_VIEW.md) |
| M12 | v0.3 能力盘点 | planned | [M12_V03_AGENT_CAPABILITY_CHECK.md](M12_V03_AGENT_CAPABILITY_CHECK.md) |
| M13 | Debug 与历史日志 | implemented | [M13_V03_DEBUG_LOGS.md](M13_V03_DEBUG_LOGS.md) |

## 历史文档

本目录中不带 `_V03_` 的模块文件来自 v0.2 文档处理主线，保留用于追溯早期实现。当前开发和页面展示应优先参考 v0.3 文档。
