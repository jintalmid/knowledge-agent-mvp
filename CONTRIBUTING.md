# Contributing

Thanks for your interest in contributing to `knowledge-agent-mvp`.

This project is a phase 0 MVP for an Agent Runner based enterprise knowledge workflow. Contributions should keep the project small, explicit, and easy to inspect.

## Development Principles

- Keep module boundaries clear.
- Prefer REST APIs or explicit `services/*` boundaries between modules.
- All LLM calls must go through `backend/app/services/llm.py`.
- All Agent tools must be registered through `backend/app/services/tool_registry.py`.
- Do not add no-LLM fallback behavior.
- Do not introduce production-only systems such as Docker sandboxing, multi-agent orchestration, formal knowledge bases, or complex permission systems unless the roadmap explicitly asks for them.
- Keep documentation updated when changing API, data model, module behavior, or page routes.

## Local Setup

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Validation

Before opening a pull request, run:

```bash
cd backend
python -m compileall app
```

```bash
cd frontend
npm run build
```

## Pull Request Checklist

- The change is scoped to the requested module or feature.
- API changes are reflected in `frontend/lib/api.ts` when needed.
- Database changes are added to `backend/app/db/sqlite.py` with safe migration behavior.
- New LLM calls write `llm_call_logs`.
- New tools are documented in `docs/modules`.
- README or module docs are updated when behavior changes.
- No secrets, uploaded files, local databases, or `.env` files are committed.

## Reporting Bugs

Please include:

- What you expected to happen.
- What actually happened.
- Steps to reproduce.
- Relevant task ID, Agent Run ID, or LLM log ID if available.
- Backend/frontend console output if relevant.

## Code of Conduct

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
