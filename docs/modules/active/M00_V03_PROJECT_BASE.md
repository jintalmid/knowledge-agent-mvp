# M00 v0.3 项目基座与配置

## 模块目标

提供 `knowledge-agent-mvp` 的 monorepo 基座、运行配置、模块注册表和健康检查能力。其他模块默认依赖 M00 提供的工程结构、配置加载和 API 前缀。

## 当前实现

- Monorepo 结构：`frontend`、`backend`、`docs`。
- 后端：FastAPI，统一 API 前缀 `/api`。
- 前端：Next.js App Router，TypeScript，Tailwind CSS。
- 数据库：SQLite，启动时由 `backend/app/db/sqlite.py` 初始化。
- 文件存储：`backend/uploads`。
- 模块注册表：`module-registry.json`。

## API

- `GET /api/health`: 返回服务健康状态。
- `GET /api/modules`: 读取 `module-registry.json` 并返回模块列表。

## 页面

- `/`: 项目入口。
- `/modules`: 模块注册表展示。

## 配置

后端配置由 `backend/app/core/config.py` 读取：

- `APP_NAME`
- `API_PREFIX`
- `LLM_PROVIDER_TYPE`
- `LLM_BASE_URL`
- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`

## 服务边界

M00 不实现业务逻辑，只提供工程约定和运行基础。其他模块不得绕过统一配置直接硬编码路径或 API 前缀。

## 非目标

- 不负责真实部署。
- 不负责 Docker 编排。
- 不负责生产级配置中心。
