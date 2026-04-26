# Backend

FastAPI service for `knowledge-agent-mvp`.

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## APIs

- `GET /api/health`
- `GET /api/modules`
- `POST /api/tasks`
- `GET /api/tasks`
- `GET /api/tasks/{task_id}`
- `PATCH /api/tasks/{task_id}`
- `DELETE /api/tasks/{task_id}`
- `POST /api/tasks/{task_id}/files`
- `GET /api/tasks/{task_id}/files`
- `GET /api/task-files/{task_file_id}`
- `DELETE /api/task-files/{task_file_id}`
- `GET /api/physical-files/{physical_file_id}`
- `POST /api/task-files/{task_file_id}/parse`
- `POST /api/tasks/{task_id}/parse-all`
- `GET /api/task-files/{task_file_id}/parsed-content`
- `GET /api/settings/llm`
- `POST /api/settings/llm/test`
- `POST /api/task-files/{task_file_id}/summarize`
- `POST /api/tasks/{task_id}/summarize-all`
- `GET /api/tasks/{task_id}/summaries`
- `GET /api/task-files/{task_file_id}/summary`
- `GET /api/llm-logs`
- `GET /api/llm-logs/{log_id}`
