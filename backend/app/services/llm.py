import time
from dataclasses import dataclass
from datetime import UTC, datetime
from sqlite3 import Connection, Row
from uuid import uuid4

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.schemas.llm import LlmCallLogRead, LlmSettingsRead


@dataclass
class LlmResult:
    text: str
    log_id: str
    provider_type: str
    model_name: str


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _preview(value: str | None, limit: int = 1200) -> str | None:
    if value is None:
        return None
    compact = value.strip()
    if len(compact) <= limit:
        return compact
    return f"{compact[:limit]}..."


def _row_to_log(row: Row) -> LlmCallLogRead:
    return LlmCallLogRead(**dict(row))


def get_llm_settings() -> LlmSettingsRead:
    settings = get_settings()
    provider_type = (settings.llm_provider_type or "").replace("-", "_") or None
    ready = all(
        [
            provider_type == "openai_compatible",
            settings.llm_base_url,
            settings.llm_api_key,
            settings.llm_model,
        ]
    )
    return LlmSettingsRead(
        provider_type=provider_type,
        base_url_configured=bool(settings.llm_base_url),
        api_key_configured=bool(settings.llm_api_key),
        model=settings.llm_model,
        ready=ready,
    )


def _insert_log(
    connection: Connection,
    task_id: str | None,
    agent_run_id: str | None,
    iteration_id: str | None,
    module_name: str,
    provider_type: str,
    model_name: str,
    prompt: str,
    response: str | None,
    status_value: str,
    error_message: str | None,
    latency_ms: int,
) -> str:
    log_id = f"llm_{uuid4().hex}"
    connection.execute(
        """
        INSERT INTO llm_call_logs (
            id,
            task_id,
            agent_run_id,
            iteration_id,
            module_name,
            provider_type,
            model_name,
            prompt_preview,
            response_preview,
            status,
            error_message,
            latency_ms,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            log_id,
            task_id,
            agent_run_id,
            iteration_id,
            module_name,
            provider_type,
            model_name,
            _preview(prompt) or "",
            _preview(response),
            status_value,
            _preview(error_message, limit=2000),
            latency_ms,
            _now_iso(),
        ),
    )
    connection.commit()
    return log_id


def _chat_completions_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def call_llm(
    connection: Connection,
    *,
    task_id: str | None,
    agent_run_id: str | None = None,
    iteration_id: str | None = None,
    module_name: str,
    system_prompt: str,
    user_prompt: str,
) -> LlmResult:
    settings = get_settings()
    provider_type = (settings.llm_provider_type or "unconfigured").replace("-", "_")
    model_name = settings.llm_model or "unconfigured"
    prompt = f"{system_prompt}\n\n{user_prompt}"
    started_at = time.perf_counter()

    def fail(message: str, code: int = status.HTTP_400_BAD_REQUEST) -> None:
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        _insert_log(
            connection=connection,
            task_id=task_id,
            agent_run_id=agent_run_id,
            iteration_id=iteration_id,
            module_name=module_name,
            provider_type=provider_type,
            model_name=model_name,
            prompt=prompt,
            response=None,
            status_value="failed",
            error_message=message,
            latency_ms=latency_ms,
        )
        raise HTTPException(status_code=code, detail=message)

    if provider_type != "openai_compatible":
        fail("LLM_PROVIDER_TYPE must be openai_compatible")
    if not settings.llm_base_url:
        fail("LLM_BASE_URL is not configured")
    if not settings.llm_api_key:
        fail("LLM_API_KEY is not configured")
    if not settings.llm_model:
        fail("LLM_MODEL is not configured")

    try:
        response = httpx.post(
            _chat_completions_url(settings.llm_base_url),
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.llm_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
            },
            timeout=settings.llm_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        text = payload["choices"][0]["message"]["content"]
    except Exception as exc:
        fail(f"LLM call failed: {exc}", code=status.HTTP_502_BAD_GATEWAY)

    latency_ms = int((time.perf_counter() - started_at) * 1000)
    log_id = _insert_log(
        connection=connection,
        task_id=task_id,
        agent_run_id=agent_run_id,
        iteration_id=iteration_id,
        module_name=module_name,
        provider_type=provider_type,
        model_name=model_name,
        prompt=prompt,
        response=text,
        status_value="success",
        error_message=None,
        latency_ms=latency_ms,
    )
    return LlmResult(text=text, log_id=log_id, provider_type=provider_type, model_name=model_name)


def list_logs(connection: Connection) -> list[LlmCallLogRead]:
    rows = connection.execute("SELECT * FROM llm_call_logs ORDER BY created_at DESC LIMIT 200").fetchall()
    return [_row_to_log(row) for row in rows]


def get_log(connection: Connection, log_id: str) -> LlmCallLogRead | None:
    row = connection.execute("SELECT * FROM llm_call_logs WHERE id = ?", (log_id,)).fetchone()
    if row is None:
        return None
    return _row_to_log(row)
