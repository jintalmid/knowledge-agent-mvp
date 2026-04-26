# M13 v0.3 Debug 与历史日志

## 模块目标

保留 LLM 调用日志，并为 Agent Run 调试信息预留统一入口。

## 当前 Step 1 范围

- 保留 `/debug/llm-logs`
- 保留 `llm_call_logs`
- 尚未新增 Agent Run Debug 页面

## 后续扩展

- 从 Agent Run 详情页跳转到相关 LLM log
- 展示每轮 prompt / response preview
- 展示工具 observation

## 非目标

- 不记录完整敏感文件内容
- 不实现日志清理策略
