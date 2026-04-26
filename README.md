# knowledge-agent-mvp

阶段 0 最小可运行项目骨架，用于验证企业知识智能平台的模块化闭环起点。

当前已实现：

- monorepo 目录：`frontend`、`backend`、`docs`
- FastAPI：`GET /api/health`、`GET /api/modules`
- Next.js 页面：`/modules`
- `module-registry.json`：M00-M13 模块注册表
- `docs/modules`：所有模块说明文件模板
- `backend/uploads`：本地文件存储目录预留
- M01 身份与权限预留：默认用户上下文
- M02 任务空间：SQLite 任务模型、任务 CRUD API、`/tasks`、`/tasks/[taskId]`
- M03 物理文件资产：SHA256 去重、本地 uploads 存储、物理文件详情 API
- M04 任务文件引用：任务文件上传、引用列表/详情/删除、`/tasks/[taskId]/files`
- M05 文件解析：文本/PDF 内容提取、CSV/Excel profile、`/tasks/[taskId]/parsing`
- M06 LLM 摘要与标签：基于解析内容调用 LLM 生成摘要、关键词、标签、分类
- M13 LLM 调用日志：统一 LLM Service、配置测试、调用日志和 Debug 页面

当前不实现问答、Excel 分析或 RAG。

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

验证：

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/modules
curl http://localhost:8000/api/tasks
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

打开：

- `http://localhost:3000`
- `http://localhost:3000/modules`
- `http://localhost:3000/tasks`
- `http://localhost:3000/tasks/{taskId}/files`
- `http://localhost:3000/tasks/{taskId}/parsing`
- `http://localhost:3000/tasks/{taskId}/summaries`
- `http://localhost:3000/settings/llm`
- `http://localhost:3000/debug/llm-logs`

如需修改后端地址，可在前端环境变量中设置：

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```
