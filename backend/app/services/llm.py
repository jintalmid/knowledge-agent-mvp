import time
from dataclasses import dataclass
from datetime import UTC, datetime
from sqlite3 import Connection, Row
from uuid import uuid4

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.schemas.llm import LlmCallLogRead, LlmSettingsRead
from app.services import model_registry


@dataclass
class LlmResult:
    text: str
    log_id: str
    provider_type: str
    model_name: str
    provider_id: str | None = None
    model_id: str | None = None
    scenario: str | None = None


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


LOG_SELECT_SQL = """
    SELECT
        l.*,
        t.name AS task_name,
        t.owner_user_id AS owner_user_id,
        t.department_id AS department_id,
        t.security_level AS security_level
    FROM llm_call_logs l
    LEFT JOIN tasks t ON t.id = l.task_id
"""


def get_llm_settings() -> LlmSettingsRead:
    settings = get_settings()
    provider_type = (settings.llm_provider_type or "").replace("-", "_") or None
    ready = bool(provider_type == "openai_compatible" and settings.llm_base_url and settings.llm_api_key and settings.llm_model)
    return LlmSettingsRead(
        provider_type=provider_type,
        config_source="backend/.env; process environment variables can override same-name settings",
        env_file_path=str(settings.model_config["env_file"]),
        base_url=settings.llm_base_url,
        base_url_configured=bool(settings.llm_base_url),
        api_key_configured=bool(settings.llm_api_key),
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
        ready=ready,
    )


def _insert_log(
    connection: Connection,
    task_id: str | None,
    agent_run_id: str | None,
    iteration_id: str | None,
    scenario: str | None,
    provider_id: str | None,
    model_id: str | None,
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
            scenario,
            provider_id,
            model_id,
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            log_id,
            task_id,
            agent_run_id,
            iteration_id,
            scenario,
            provider_id,
            model_id,
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
    scenario: str = "default_text",
    model_id_override: str | None = None,
    module_name: str,
    system_prompt: str,
    user_prompt: str,
) -> LlmResult:
    prompt = f"{system_prompt}\n\n{user_prompt}"
    started_at = time.perf_counter()
    try:
        if model_id_override:
            resolved = model_registry.resolve_model_by_id(connection, model_id_override, scenario=scenario)
        else:
            resolved = model_registry.resolve_model_for_scenario(connection, scenario)
    except HTTPException as exc:
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        _insert_log(
            connection=connection,
            task_id=task_id,
            agent_run_id=agent_run_id,
            iteration_id=iteration_id,
            scenario=scenario,
            provider_id=None,
            model_id=None,
            module_name=module_name,
            provider_type="unconfigured",
            model_name="unconfigured",
            prompt=prompt,
            response=None,
            status_value="failed",
            error_message=str(exc.detail),
            latency_ms=latency_ms,
        )
        raise

    provider_type = resolved.provider_type.replace("-", "_")
    model_name = resolved.model_name

    def fail(message: str, code: int = status.HTTP_400_BAD_REQUEST) -> None:
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        _insert_log(
            connection=connection,
            task_id=task_id,
            agent_run_id=agent_run_id,
            iteration_id=iteration_id,
            scenario=scenario,
            provider_id=resolved.provider_id,
            model_id=resolved.model_id,
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
        fail(f"provider_type is reserved but not implemented: {provider_type}")
    if not resolved.base_url:
        fail("LLM base_url is not configured")
    if not resolved.api_key:
        fail("LLM API key is not configured")
    if not resolved.model_name:
        fail("LLM model_name is not configured")

    try:
        response = httpx.post(
            _chat_completions_url(resolved.base_url),
            headers={
                "Authorization": f"Bearer {resolved.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": resolved.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
            },
            timeout=get_settings().llm_timeout_seconds,
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
        scenario=scenario,
        provider_id=resolved.provider_id,
        model_id=resolved.model_id,
        module_name=module_name,
        provider_type=provider_type,
        model_name=model_name,
        prompt=prompt,
        response=text,
        status_value="success",
        error_message=None,
        latency_ms=latency_ms,
    )
    return LlmResult(
        text=text,
        log_id=log_id,
        provider_type=provider_type,
        model_name=model_name,
        provider_id=resolved.provider_id,
        model_id=resolved.model_id,
        scenario=scenario,
    )


def list_logs(
    connection: Connection,
    *,
    scenario: str | None = None,
    model_id: str | None = None,
    provider_id: str | None = None,
) -> list[LlmCallLogRead]:
    clauses = []
    params: list[str] = []
    if scenario:
        clauses.append("l.scenario = ?")
        params.append(scenario)
    if model_id:
        clauses.append("l.model_id = ?")
        params.append(model_id)
    if provider_id:
        clauses.append("l.provider_id = ?")
        params.append(provider_id)
    where_sql = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = connection.execute(f"{LOG_SELECT_SQL}{where_sql} ORDER BY l.created_at DESC LIMIT 200", params).fetchall()
    return [_row_to_log(row) for row in rows]


def get_log(connection: Connection, log_id: str) -> LlmCallLogRead | None:
    row = connection.execute(f"{LOG_SELECT_SQL} WHERE l.id = ?", (log_id,)).fetchone()
    if row is None:
        return None
    return _row_to_log(row)
