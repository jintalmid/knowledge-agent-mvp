# M00 项目基座与配置

## 模块目标

提供 monorepo 基座、后端 API 入口、前端页面入口、配置样例、模块注册表和文件存储目录预留。

## 当前 Step 0 范围

- 后端提供 `GET /api/health`
- 后端提供 `GET /api/modules`
- 前端提供 `/modules`
- 维护根目录 `module-registry.json`
- 预留 `backend/uploads`

## 对外接口

- `GET /api/health`
- `GET /api/modules`

## 非目标

不实现任务、上传、解析、LLM、检索、问答、Excel 分析或日志业务。

## 扩展预留

- `.env` 中预留 LLM Provider 配置
- `backend/uploads` 作为本地文件存储根目录
- `module-registry.json` 作为模块发现入口
