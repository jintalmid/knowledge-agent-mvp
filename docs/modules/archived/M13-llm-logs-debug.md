# M13 LLM 调用日志与 Debug

## 模块目标

记录所有 LLM 调用的请求摘要、响应摘要、耗时、错误和关联业务对象，提供 Debug 基础。

## 当前 Step 0 范围

仅保留说明文件和注册表条目。

## 对外接口

暂无。

## 非目标

不实现日志表、日志写入、日志查询或 Debug 页面。

## 扩展预留

所有 LLM 调用必须通过统一 LLM Service 写入日志，后续字段应预留 `provider`、`model`、`prompt_tokens`、`completion_tokens`、`latency_ms`、`error`。
