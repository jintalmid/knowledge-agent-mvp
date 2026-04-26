# M00 v0.3 项目基座与配置

## 模块目标

保留现有 monorepo、FastAPI、Next.js、SQLite、本地 uploads、环境变量和模块注册表，为 AutoGPT / ReAct 阶段 0 提供运行底座。

## 当前 Step 1 范围

- 不重建项目
- 不更换技术栈
- 保留现有 `/api/health`、`/api/modules`
- `module-registry.json` 迁移为 v0.3 Agent Runner 模块结构

## 对外接口

- `GET /api/health`
- `GET /api/modules`

## 非目标

- 不引入多服务部署
- 不实现 Docker 沙箱
- 不实现后台队列
