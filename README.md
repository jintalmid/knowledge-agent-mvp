# knowledge-agent-mvp

`knowledge-agent-mvp` 是一个阶段 0 最小可运行项目。当前主线已经从 v0.2 的“文档处理 + 检索 + 问答”迁移为 v0.3 的 “AutoGPT / ReAct Agent Runner” 验证版。

项目目标不是做完整知识库产品，而是验证一个企业知识智能平台的最小闭环：

1. 创建任务空间。
2. 上传文件并自动解析。
3. 生成文件摘要。
4. 通过统一 LLM Service 调用模型并记录日志。
5. 由 Agent Runner 按 `plan -> tool call -> observation -> reflection -> decision` 循环执行。
6. 调用 `read_text_file` 或 `analyze_excel_file` 工具。
7. 保存最终 Markdown 答案、来源和每轮运行过程。

## 当前定位

当前版本是 v0.3 阶段 0：

- 保留 FastAPI、Next.js、SQLite、本地文件存储。
- 保留文件上传、基础解析、摘要、Excel 受限代码执行能力。
- 新增 Agent Run、Iteration、Observation 数据模型。
- 新增 Tool Registry 和 Agent Runner。
- 降级正式知识库、复杂权限、正式 RAG、Embedding/Hybrid 检索、多 Agent 编排为未来预留。

## 技术栈

- Frontend: Next.js, TypeScript, Tailwind CSS
- Backend: FastAPI, Python
- Database: SQLite
- File Storage: `backend/uploads`
- LLM: OpenAI-compatible API adapter
- Excel Sandbox: LLM 生成 Python，经静态检查后在受限临时目录中执行

## 目录结构

```text
knowledge-agent-mvp/
  backend/                 FastAPI 后端
    app/
      api/                 REST API 路由
      core/                配置与默认身份上下文
      db/                  SQLite 初始化与迁移
      models/              枚举和轻量模型
      schemas/             Pydantic 请求/响应模型
      services/            业务服务边界
    uploads/               本地上传文件存储
    knowledge_agent_mvp.sqlite3
    .env.example
    README.md
  frontend/                Next.js 前端
    app/                   App Router 页面
    lib/                   API client 与浏览器工具
    README.md
  docs/
    README.md
    03_ORCHESTRATION_PLAN.md
    modules/               M00-M13 模块说明
  module-registry.json     当前模块注册表
  README.md
```

## 一键部署

Ubuntu 服务器上直接执行：

```bash
wget -qO- https://raw.githubusercontent.com/jintalmid/knowledge-agent-mvp/main/scripts/install_ubuntu.sh | bash
```

脚本会一步步引导完成：

- 从 GitHub 下载项目。
- 安装 Python、Node.js、npm 等依赖。
- 创建后端虚拟环境并安装 `requirements.txt`。
- 生成 `backend/.env`，配置 LLM 地址、API Key、默认模型和超时时间。
- 生成 `frontend/.env.local`，配置前端访问后端的地址。
- 初始化 SQLite 数据库。
- 构建前端，并输出前后端启动命令。
- 可选通过 `ufw` 开放外部访问端口。

脚本会自己从 GitHub 下载项目内容，不需要先手动 `git clone`。如果系统没有 `wget`，可用：

```bash
curl -fsSL https://raw.githubusercontent.com/jintalmid/knowledge-agent-mvp/main/scripts/install_ubuntu.sh | bash
```

如果仓库是私有仓库，需要先完成 GitHub 登录，或在脚本提示 `GitHub repository URL` 时填写有权限的 clone 地址。

## 删除

一行删除命令：

```bash
wget -qO- https://raw.githubusercontent.com/jintalmid/knowledge-agent-mvp/main/scripts/install_ubuntu.sh | bash -s -- --uninstall
```

安全限制：

- 安装目录必须位于当前用户的 `$HOME` 下，例如 `$HOME/knowledge-agent-mvp`。
- 默认不会覆盖非空的普通目录。
- 卸载只允许删除 `$HOME` 下的安装目录，并要求输入 `DELETE` 二次确认。

## 快速启动

### 1. 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

后端地址：

```text
http://localhost:8000
```

### 2. 配置 LLM

编辑 `backend/.env`：

```env
LLM_PROVIDER_TYPE=openai_compatible
LLM_BASE_URL=https://your-openai-compatible-endpoint/v1
LLM_API_KEY=your-api-key
LLM_MODEL=your-model
LLM_TIMEOUT_SECONDS=180
```

没有 LLM 配置时，摘要、工具读取、Agent Runner、Excel 代码生成都会明确报错，不做本地 fallback。

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端地址：

```text
http://localhost:3000
```

如需修改后端地址：

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

## 常用页面

- `/modules`: 模块注册表
- `/tasks`: 任务列表
- `/tasks/{taskId}`: 任务详情
- `/tasks/{taskId}/files`: 文件上传、自动解析状态与任务文件引用
- `/tasks/{taskId}/parsing`: 文件解析 Debug、批量重试和 profile/text preview
- `/tasks/{taskId}/summaries`: LLM 摘要与标签
- `/tasks/{taskId}/agent`: 启动 Agent Run
- `/tasks/{taskId}/runs/{runId}`: Agent Run 详情
- `/tasks/{taskId}/results`: 历史结果与来源
- `/tasks/{taskId}/excel`: 单文件 Excel 分析
- `/settings/llm`: LLM 配置状态与测试
- `/debug/llm-logs`: LLM 调用日志

## 常用 API

基础：

- `GET /api/health`
- `GET /api/modules`

任务：

- `POST /api/tasks`
- `GET /api/tasks`
- `GET /api/tasks/{task_id}`
- `PATCH /api/tasks/{task_id}`
- `DELETE /api/tasks/{task_id}`

文件：

- `POST /api/tasks/{task_id}/files`
- `GET /api/tasks/{task_id}/files`
- `GET /api/task-files/{task_file_id}`
- `DELETE /api/task-files/{task_file_id}`
- `GET /api/physical-files/{physical_file_id}`

解析与摘要：

- `POST /api/task-files/{task_file_id}/parse`
- `POST /api/tasks/{task_id}/parse-all`
- `GET /api/task-files/{task_file_id}/parsed-content`
- `POST /api/task-files/{task_file_id}/summarize`
- `POST /api/tasks/{task_id}/summarize-all`
- `GET /api/tasks/{task_id}/summaries`
- `GET /api/task-files/{task_file_id}/summary`

Agent：

- `GET /api/tools`
- `POST /api/tools/{tool_name}/call`
- `POST /api/tasks/{task_id}/agent-runs`
- `GET /api/agent-runs/{run_id}`

结果与日志：

- `GET /api/tasks/{task_id}/results`
- `GET /api/answers/{answer_id}`
- `GET /api/llm-logs`
- `GET /api/llm-logs/{log_id}`

## 模块说明

当前模块以 v0.3 注册表为准：

- M00 项目基座与配置
- M01 身份与权限预留
- M02 Agent 任务空间
- M03 文件资产与解析支撑
- M04 LLM Service 与调用日志
- M05 Tool Registry Service
- M06 Agent Run 数据模型
- M07 Agent Runner Service
- M08 ReAct Iteration Loop
- M09 `read_text_file` 工具
- M10 `analyze_excel_file` 工具
- M11 Agent Run 详情与结果展示
- M12 v0.3 能力盘点
- M13 Debug 与历史日志

逐模块文档见 [docs/modules/README.md](docs/modules/README.md)。

## 验证命令

后端：

```bash
cd backend
python -m compileall app
curl http://localhost:8000/api/health
curl http://localhost:8000/api/settings/llm
```

前端：

```bash
cd frontend
npm run build
```

## 开源与社区

本项目按 GitHub 常见开源仓库结构补充了基础社区文件：

- [LICENSE](LICENSE): MIT License。
- [CONTRIBUTING.md](CONTRIBUTING.md): 贡献指南、开发原则和 PR 检查项。
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md): 社区行为准则。
- [SECURITY.md](SECURITY.md): 安全报告方式、MVP 安全边界和已知限制。
- [SUPPORT.md](SUPPORT.md): 支持范围和提问入口。
- [.github/ISSUE_TEMPLATE](.github/ISSUE_TEMPLATE): Bug report 和 feature request 模板。
- [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md): PR 模板。
- [.github/dependabot.yml](.github/dependabot.yml): npm 和 pip 依赖更新配置。

## 当前非目标

- 不做正式知识库。
- 不做多部门真实权限。
- 不做模板管理。
- 不做 Docker 沙箱。
- 不做多 Agent 编排。
- 不做本地桌面 App。
- 不做无 LLM fallback。

## 安全注意

- 不要提交真实 `backend/.env`。
- LLM API key 只应保存在本地环境文件中。
- Excel 沙箱只允许有限 imports，禁止 `os`、`sys`、`subprocess`、`socket`、`requests`、`shutil`、`pathlib`、`eval`、`exec`、`__import__`、`importlib`。
- Excel 代码只允许写 `result.json`。
