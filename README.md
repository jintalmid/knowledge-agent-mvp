# knowledge-agent-mvp

`knowledge-agent-mvp` 是一个阶段 0 最小可运行项目。当前主线已经从 v0.2 的“文档处理 + 检索 + 问答”迁移为 v0.3 的 “AutoGPT / ReAct Agent Runner” 验证版。

项目目标不是做完整知识库产品，而是验证一个企业知识智能平台的最小闭环：

1. 创建任务空间。
2. 上传文件并自动解析。
3. 生成文件摘要。
4. 通过模型注册表和场景路由选择模型，并记录 LLM 调用日志。
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
- LLM: OpenAI-compatible Provider, model registry, scenario routing
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
    modules/
      active/              v0.3 当前唯一模块调用契约
      archived/            v0.2 历史模块文档
  module-registry.json     当前模块注册表
  README.md
```

## 一键部署

Ubuntu 服务器上直接执行：

```bash
wget -qO- https://raw.githubusercontent.com/jintalmid/knowledge-agent-mvp/main/scripts/install_ubuntu.sh | bash
```

当前脚本版本：`2026-04-28.8`，更新时间 UTC：`2026-04-28 04:31:00 UTC`。脚本运行时会在最前面打印版本、基于本机时区转换后的更新时间和 UTC 更新时间，方便确认是否拉到了最新版。

脚本会一步步引导完成：

- 从 GitHub 下载项目。
- 安装 Python、Node.js、npm 等依赖。
- 创建后端虚拟环境并安装 `requirements.txt`。
- 生成 `backend/.env`，配置初始 OpenAI-compatible Provider、API Key、默认文本模型和超时时间。
- 生成 `frontend/.env.local`，配置前端访问后端的地址。
- 初始化 SQLite 数据库。
- 构建前端，并输出前后端启动命令。
- 可选通过 `ufw` 开放外部访问端口。

脚本会自己从 GitHub 下载项目内容，不需要先手动 `git clone`。如果系统没有 `wget`，可用：

```bash
curl -fsSL https://raw.githubusercontent.com/jintalmid/knowledge-agent-mvp/main/scripts/install_ubuntu.sh | bash
```

如果仓库是私有仓库，需要先完成 GitHub 登录，或在脚本提示 `GitHub repository URL` 时填写有权限的 clone 地址。

### WSL 注意事项

如果 Ubuntu 安装在 Windows WSL 中，脚本会默认把 `public host` 设置为 `localhost`。同时，前端会写入 `NEXT_PUBLIC_API_BASE_URL=auto:8000`，浏览器会根据当前打开页面的主机名自动访问后端：

- 打开 `http://localhost:3000` 时，前端请求 `http://localhost:8000`。
- 打开 `http://<Windows 当前 IP>:3000` 时，前端请求 `http://<Windows 当前 IP>:8000`。

这样 Windows WiFi IP 变化时，一般不需要重新修改前端配置。只要用新的访问地址打开前端，后端地址会自动跟随当前浏览器 host。

`auto:8000` 在 Next.js 服务端渲染时会使用 `http://127.0.0.1:8000` 访问后端，在浏览器端会使用当前页面的 host 访问后端。

在 WSL 里验证后端：

```bash
curl -s http://127.0.0.1:8000/api/settings/llm
```

在 Windows PowerShell 里验证浏览器同侧链路：

```powershell
curl.exe http://localhost:8000/api/settings/llm
```

如果 WSL 里正常、PowerShell 里不正常，问题通常是 WSL 端口转发、Windows 防火墙或服务没有监听到可被 Windows 访问的地址。

## 一键更新

如果已经部署过，可以基于当前安装目录拉取最新版本：

```bash
wget -qO- https://raw.githubusercontent.com/jintalmid/knowledge-agent-mvp/main/scripts/install_ubuntu.sh | bash -s -- --update
```

更新流程会执行：

- 如果后端或前端正在运行，先停止。
- `git pull --ff-only` 拉取最新代码。
- 更新后端 Python 依赖。
- 执行 SQLite 初始化/迁移。
- 更新前端 npm 依赖。
- 使用 webpack 重新构建前端。
- 如果更新前服务正在运行，更新后自动重新启动。

如果安装在非默认目录，需要加 `--install-dir`：

```bash
wget -qO- https://raw.githubusercontent.com/jintalmid/knowledge-agent-mvp/main/scripts/install_ubuntu.sh | bash -s -- --update --install-dir "$HOME/apps/knowledge-agent-mvp"
```

## 命令行诊断 LLM

日常新增、编辑和测试模型请优先使用前端：

- `/settings/models`: 管理 Provider 和 Provider 下的模型，并测试单个模型。
- `/settings/model-routing`: 为 `file_summary`、`agent_planning`、`excel_code_generation` 等业务场景选择模型，并测试路由。

`scripts/test_llm_env.sh` 仍然保留，但定位是底层排障脚本。它只读取 `backend/.env`，直接测试 OpenAI-compatible `/chat/completions` 连通性，不读取数据库里的模型注册表和场景路由。

当页面显示模型不可用、WSL/Ubuntu 网络不通、或者怀疑 `.env` 没被正确读取时，可以绕过前端和数据库直接验证：

```bash
cd "$HOME/knowledge-agent-mvp"
bash scripts/test_llm_env.sh
```

脚本会自动使用 `backend/.venv/bin/python`，读取 `backend/.env`，隐藏 API Key，并直接调用 OpenAI-compatible `/chat/completions`。

可选参数：

```bash
bash scripts/test_llm_env.sh --timeout 300
bash scripts/test_llm_env.sh --message "Reply only: ok"
bash scripts/test_llm_env.sh --env "$HOME/knowledge-agent-mvp/backend/.env"
```

## 一键启动 / 查看 / 停止

安装完成后，脚本会把端口、host 和访问地址保存到 `$HOME/knowledge-agent-mvp/.runtime/app.env`。之后可以用同一个脚本管理服务。

一键启动：

```bash
wget -qO- https://raw.githubusercontent.com/jintalmid/knowledge-agent-mvp/main/scripts/install_ubuntu.sh | bash -s -- --start
```

一键查看是否启动：

```bash
wget -qO- https://raw.githubusercontent.com/jintalmid/knowledge-agent-mvp/main/scripts/install_ubuntu.sh | bash -s -- --status
```

一键停止：

```bash
wget -qO- https://raw.githubusercontent.com/jintalmid/knowledge-agent-mvp/main/scripts/install_ubuntu.sh | bash -s -- --stop
```

如果安装在非默认目录，需要加 `--install-dir`：

```bash
wget -qO- https://raw.githubusercontent.com/jintalmid/knowledge-agent-mvp/main/scripts/install_ubuntu.sh | bash -s -- --status --install-dir "$HOME/apps/knowledge-agent-mvp"
```

当前脚本使用 pid 文件管理后台进程，日志位于 `$HOME/knowledge-agent-mvp/.runtime/`。正式生产部署更常见的方式是 `systemd`；容器化部署更常见的是 `docker compose up/down/ps`。

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

### 2. 配置初始 LLM

编辑 `backend/.env`：

```env
LLM_PROVIDER_TYPE=openai_compatible
LLM_BASE_URL=https://your-openai-compatible-endpoint/v1
LLM_API_KEY=your-api-key
LLM_MODEL=your-model
LLM_TIMEOUT_SECONDS=180
```

启动后端时，系统会把这组 `.env` 配置种子化为一个默认 Provider 和一个 `default_text` 模型。之后更推荐在页面中维护模型：

- `/settings/models`: 新增 Provider、在 Provider 下新增模型、设置模型类型、能力 tags、context/output window、测试模型。
- `/settings/model-routing`: 为不同业务场景选择专用模型；未配置专用模型时回退到 `default_text`。
- `/settings/llm`: legacy `.env` 状态查看和诊断入口。

没有可用的 `default_text` 模型时，摘要、工具读取、Agent Runner、Excel 代码生成都会明确报错，不做本地 fallback。

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
- `/settings/models`: Provider 与模型管理
- `/settings/model-routing`: 场景模型路由
- `/settings/llm`: legacy `.env` 配置状态与诊断
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

模型与路由：

- `GET /api/model-providers`
- `POST /api/model-providers`
- `GET /api/model-providers/{provider_id}`
- `PATCH /api/model-providers/{provider_id}`
- `DELETE /api/model-providers/{provider_id}`
- `GET /api/models`
- `POST /api/models`
- `GET /api/models/{model_id}`
- `PATCH /api/models/{model_id}`
- `DELETE /api/models/{model_id}`
- `POST /api/models/{model_id}/test`
- `GET /api/model-scenarios`
- `GET /api/model-routes`
- `PATCH /api/model-routes/{scenario}`
- `POST /api/model-routes/{scenario}/test`
- `GET /api/settings/llm`
- `POST /api/settings/llm/test`

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
- M04 模型注册、模型路由、LLM Service 与调用日志
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
