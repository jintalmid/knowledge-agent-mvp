# Documentation

本目录保存 `knowledge-agent-mvp` 的架构说明、模块说明和阶段计划。

当前文档主线是 v0.3：AutoGPT / ReAct 阶段 0 版。早期 v0.2 文件处理文档保留在 `docs/modules/archived/` 中作为历史上下文，但当前模块注册表以 `module-registry.json` 和 `docs/modules/active/` 为准。

## 文档入口

- [模块说明索引](modules/README.md)
- [编排与能力计划](03_ORCHESTRATION_PLAN.md)
- [LLM Provider 设计](07_LLM_PROVIDER_DESIGN.md)
- [Debug 日志设计](11_DEBUG_LOGGING_DESIGN.md)
- [项目 README](../README.md)
- [后端 README](../backend/README.md)
- [前端 README](../frontend/README.md)

## 阅读顺序

1. 先读根目录 [README](../README.md)，理解项目定位和启动方式。
2. 再读 [模块说明索引](modules/README.md)，查看 M00-M13 的边界。
3. 需要调后端时读 [backend/README](../backend/README.md)。
4. 需要调页面时读 [frontend/README](../frontend/README.md)。

## 文档约定

- 每个模块说明只描述自身能力和调用边界。
- 模块之间通过 REST API 或 `services/*` 服务边界协作。
- 涉及 LLM 的能力必须声明日志记录方式。
- 当前 LLM 主入口是模型注册表和场景路由；`.env` 只作为初始种子配置和底层诊断来源。
- 未实现的最终态能力必须标为预留或非目标。
