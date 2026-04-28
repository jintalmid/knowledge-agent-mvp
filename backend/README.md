# Backend

FastAPI 后端负责 `knowledge-agent-mvp` 的数据模型、文件处理、LLM 调用、工具注册、Agent Runner 和结果保存。

## 职责

- 初始化和迁移 SQLite 表。
- 提供任务空间 CRUD。
- 管理上传文件、物理文件资产和任务文件引用。
- 上传成功后自动调用解析服务解析文本、PDF、CSV、Excel。
- 通过模型注册表和场景路由调用统一 LLM Service，生成摘要、工具 observation、Excel 分析代码、Agent plan/reflection/final answer。
- 记录所有 LLM 调用日志。
- 注册并执行 Agent 工具。
- 执行 Agent Run 主循环。
- 执行 Excel 受限代码沙箱。

## 运行

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

## 环境变量与模型配置

```env
LLM_PROVIDER_TYPE=openai_compatible
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
LLM_TIMEOUT_SECONDS=180
```

说明：

- `LLM_PROVIDER_TYPE` 当前只支持 `openai_compatible`。
- `LLM_BASE_URL` 可以是 OpenAI-compatible endpoint，例如 `https://example.com/v1`。
- `LLM_API_KEY` 是服务商密钥。
- `LLM_MODEL` 是模型名。
- `LLM_TIMEOUT_SECONDS` 控制单次 LLM HTTP 调用超时。
- 后端启动时会把 `.env` 配置种子化为默认 Provider 和 `default_text` 模型。
- 正式业务调用不直接读 `LLM_MODEL`，而是通过 `model_route_configs.scenario` 路由到具体模型。
- 如果某个业务场景没有专用模型，会 fallback 到 `default_text`；如果 `default_text` 不可用，会明确报错。
- `scripts/test_llm_env.sh` 只用于底层 `.env` 和网络诊断，不代表数据库模型路由一定可用。

## 主要目录

```text
app/
  api/        FastAPI routers
  core/       配置、默认用户上下文
  db/         SQLite connection、init_db、轻量迁移
  models/     任务状态等轻量模型
  schemas/    Pydantic 请求和响应模型
  services/   业务服务边界
uploads/      SHA256 分目录保存的本地文件
```

## 数据表

- `tasks`
- `physical_files`
- `task_files`
- `parsed_contents`
- `file_summaries`
- `file_summary_extras`
- `document_chunks`
- `embedding_records`
- `retrieval_settings`
- `model_providers`
- `model_configs`
- `model_route_configs`
- `questions`
- `answers`
- `excel_analysis_runs`
- `agent_runs`
- `agent_iterations`
- `observations`
- `llm_call_logs`

## API 总览

基础：

- `GET /api/health`
- `GET /api/modules`

模型与 LLM：

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
- `GET /api/llm-logs`
- `GET /api/llm-logs/{log_id}`

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

解析：

- `POST /api/task-files/{task_file_id}/parse`
- `POST /api/tasks/{task_id}/parse-all`
- `GET /api/task-files/{task_file_id}/parsed-content`

摘要：

- `POST /api/task-files/{task_file_id}/summarize`
- `POST /api/tasks/{task_id}/summarize-all`
- `GET /api/tasks/{task_id}/summaries`
- `GET /api/task-files/{task_file_id}/summary`

工具与 Agent：

- `GET /api/tools`
- `POST /api/tools/{tool_name}/call`
- `POST /api/tasks/{task_id}/agent-runs`
- `GET /api/agent-runs/{run_id}`

结果：

- `POST /api/tasks/{task_id}/ask`
- `GET /api/tasks/{task_id}/results`
- `GET /api/answers/{answer_id}`
- `POST /api/task-files/{task_file_id}/excel/analyze`

预留能力：

- `POST /api/task-files/{task_file_id}/chunks`
- `GET /api/task-files/{task_file_id}/chunks`
- `GET /api/settings/retrieval`
- `PATCH /api/settings/retrieval`
- `POST /api/tasks/{task_id}/retrieve`
- `GET /api/tasks/{task_id}/capability-check`
- `GET /api/phase0/requirements`

## 服务边界

- `services/llm.py`: 统一 LLM Service 和调用日志。
- `services/model_registry.py`: Provider、模型、scenario 路由和 default_text fallback。
- `services/tool_registry.py`: 工具注册和工具调用。
- `services/agent_runner.py`: Agent Run 主循环。
- `services/excel_analysis.py`: Excel 代码生成、安全检查、受限执行。
- `services/parsing.py`: 文件解析。
- `services/summaries.py`: 文件摘要。
- `services/files.py`: 文件上传、SHA256 去重和引用。
- `services/files.py` 上传成功后只负责编排调用 `services/parsing.py`，不内联解析逻辑。
- `services/qa.py`: v0.2 文本问答能力，当前作为兼容能力保留。

## 验证

```bash
python -m compileall app
curl http://localhost:8000/api/health
curl http://localhost:8000/api/modules
curl http://localhost:8000/api/models
curl http://localhost:8000/api/model-routes
```

## 注意

- 不要提交 `backend/.env`。
- 所有 LLM 调用必须走 `services/llm.py`。
- 所有 LLM 调用必须传入 `scenario`，由 `services/model_registry.py` 解析模型。
- 所有 Agent 工具必须通过 `services/tool_registry.py` 注册。
- Excel 代码执行必须经过静态检查和受限子进程。
