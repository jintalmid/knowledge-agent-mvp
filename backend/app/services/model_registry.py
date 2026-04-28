import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from sqlite3 import Connection, Row
from uuid import uuid4

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.db.sqlite import MODEL_SCENARIO_DEFINITIONS
from app.schemas.models import (
    ModelConfigCreate,
    ModelConfigRead,
    ModelConfigUpdate,
    ModelProviderCreate,
    ModelProviderRead,
    ModelProviderUpdate,
    ModelRouteRead,
    ModelRouteUpdate,
    ModelScenarioRead,
)


@dataclass(frozen=True)
class ResolvedModel:
    scenario: str
    provider_id: str
    model_id: str
    provider_type: str
    base_url: str
    api_key: str
    model_name: str
    display_name: str
    source: str
    route_chain: list[str]


SCENARIO_DESCRIPTIONS = {
    "default_text": "Required fallback text LLM for all text-generation scenarios.",
    "file_summary": "Summarize parsed files and generate keywords/tags.",
    "agent_planning": "Generate Agent plan JSON for each ReAct iteration.",
    "agent_reflection": "Reflect on tool observations and decide whether to continue.",
    "final_answer": "Generate the final Markdown answer for an Agent Run.",
    "text_tool": "Extract observations and evidence from parsed text files.",
    "excel_code_generation": "Generate Python analysis code for Excel-compatible files.",
    "excel_code_repair": "Repair malformed Excel code JSON or failed sandbox code.",
    "excel_result_explanation": "Reserved for explaining Excel results with LLM.",
    "document_parse_vision": "Reserved for multimodal document parsing.",
    "embedding_generation": "Reserved for embedding generation.",
    "retrieval_rerank": "Reserved for reranking retrieval candidates.",
    "ppt_parse": "Reserved for PPT parsing with vision/multimodal models.",
    "pdf_image_parse": "Reserved for PDF image parsing with vision/multimodal models.",
    "ocr": "Reserved for OCR-capable models.",
}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item).strip()]


def _json_dumps_list(value: list[str] | None) -> str:
    return json.dumps([str(item).strip() for item in value or [] if str(item).strip()], ensure_ascii=False)


def _bool(value: object) -> bool:
    return bool(int(value or 0))


def _resolve_api_key(provider: Row) -> str | None:
    inline_key = provider["api_key"]
    if inline_key:
        return str(inline_key)
    env_name = provider["api_key_env_name"]
    if not env_name:
        return None
    if env_name == "LLM_API_KEY":
        return get_settings().llm_api_key or os.environ.get(env_name)
    return os.environ.get(str(env_name))


def _provider_row_to_read(row: Row) -> ModelProviderRead:
    return ModelProviderRead(
        id=row["id"],
        name=row["name"],
        provider_type=row["provider_type"],
        base_url=row["base_url"],
        api_key_env_name=row["api_key_env_name"],
        api_key_configured=bool(row["api_key"]) or bool(_resolve_api_key(row)),
        enabled=_bool(row["enabled"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _model_row_to_read(row: Row) -> ModelConfigRead:
    return ModelConfigRead(
        id=row["id"],
        provider_id=row["provider_id"],
        provider_name=row["provider_name"] if "provider_name" in row.keys() else None,
        provider_type=row["provider_type"] if "provider_type" in row.keys() else None,
        display_name=row["display_name"],
        model_name=row["model_name"],
        model_types_json=_json_list(row["model_types_json"]),
        capability_tags_json=_json_list(row["capability_tags_json"]),
        context_window=row["context_window"],
        output_window=row["output_window"] if "output_window" in row.keys() else None,
        enabled=_bool(row["enabled"]),
        is_default_text_model=_bool(row["is_default_text_model"]),
        last_test_status=row["last_test_status"],
        last_test_message=row["last_test_message"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _route_health(row: Row) -> tuple[str, str]:
    if not _bool(row["enabled"]):
        return "disabled", "route disabled"
    if not row["model_id"]:
        if row["fallback_scenario"]:
            return "fallback", f"uses fallback scenario: {row['fallback_scenario']}"
        if _bool(row["is_required"]):
            return "missing", "required scenario has no model"
        return "optional", "optional capability reserved; no model configured"
    if not row["model_enabled"]:
        return "failed", "configured model is disabled"
    if not row["provider_enabled"]:
        return "failed", "configured provider is disabled"
    return "ok", "configured"


def _route_row_to_read(row: Row) -> ModelRouteRead:
    health_status, health_message = _route_health(row)
    return ModelRouteRead(
        id=row["id"],
        scenario=row["scenario"],
        model_id=row["model_id"],
        model_display_name=row["model_display_name"],
        model_name=row["model_name"],
        provider_id=row["provider_id"],
        provider_name=row["provider_name"],
        required_tags_json=_json_list(row["required_tags_json"]),
        is_required=_bool(row["is_required"]),
        fallback_scenario=row["fallback_scenario"],
        enabled=_bool(row["enabled"]),
        health_status=health_status,
        health_message=health_message,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


MODEL_SELECT_SQL = """
    SELECT
        m.*,
        p.name AS provider_name,
        p.provider_type AS provider_type
    FROM model_configs m
    LEFT JOIN model_providers p ON p.id = m.provider_id
"""


ROUTE_SELECT_SQL = """
    SELECT
        r.*,
        m.display_name AS model_display_name,
        m.model_name AS model_name,
        m.enabled AS model_enabled,
        p.id AS provider_id,
        p.name AS provider_name,
        p.enabled AS provider_enabled
    FROM model_route_configs r
    LEFT JOIN model_configs m ON m.id = r.model_id
    LEFT JOIN model_providers p ON p.id = m.provider_id
"""


def list_providers(connection: Connection) -> list[ModelProviderRead]:
    rows = connection.execute("SELECT * FROM model_providers ORDER BY created_at DESC").fetchall()
    return [_provider_row_to_read(row) for row in rows]


def get_provider(connection: Connection, provider_id: str) -> ModelProviderRead | None:
    row = connection.execute("SELECT * FROM model_providers WHERE id = ?", (provider_id,)).fetchone()
    return _provider_row_to_read(row) if row else None


def create_provider(connection: Connection, payload: ModelProviderCreate) -> ModelProviderRead:
    provider_id = f"provider_{uuid4().hex}"
    now = _now_iso()
    connection.execute(
        """
        INSERT INTO model_providers (
            id, name, provider_type, base_url, api_key_env_name, api_key, enabled, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            provider_id,
            payload.name.strip(),
            payload.provider_type.strip().replace("-", "_"),
            payload.base_url.strip(),
            payload.api_key_env_name.strip() if payload.api_key_env_name else None,
            payload.api_key.strip() if payload.api_key else None,
            1 if payload.enabled else 0,
            now,
            now,
        ),
    )
    provider = get_provider(connection, provider_id)
    if provider is None:
        raise HTTPException(status_code=500, detail="failed to create provider")
    return provider


def update_provider(connection: Connection, provider_id: str, payload: ModelProviderUpdate) -> ModelProviderRead:
    existing = connection.execute("SELECT * FROM model_providers WHERE id = ?", (provider_id,)).fetchone()
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="provider not found")
    connection.execute(
        """
        UPDATE model_providers
        SET name = ?,
            provider_type = ?,
            base_url = ?,
            api_key_env_name = ?,
            api_key = ?,
            enabled = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            payload.name.strip() if payload.name is not None else existing["name"],
            payload.provider_type.strip().replace("-", "_") if payload.provider_type is not None else existing["provider_type"],
            payload.base_url.strip() if payload.base_url is not None else existing["base_url"],
            payload.api_key_env_name.strip() if payload.api_key_env_name is not None and payload.api_key_env_name.strip() else existing["api_key_env_name"],
            payload.api_key.strip() if payload.api_key is not None and payload.api_key.strip() else existing["api_key"],
            1 if (payload.enabled if payload.enabled is not None else _bool(existing["enabled"])) else 0,
            _now_iso(),
            provider_id,
        ),
    )
    provider = get_provider(connection, provider_id)
    if provider is None:
        raise HTTPException(status_code=500, detail="failed to update provider")
    return provider


def delete_provider(connection: Connection, provider_id: str) -> bool:
    cursor = connection.execute("DELETE FROM model_providers WHERE id = ?", (provider_id,))
    return cursor.rowcount > 0


def list_models(connection: Connection) -> list[ModelConfigRead]:
    rows = connection.execute(f"{MODEL_SELECT_SQL} ORDER BY m.created_at DESC").fetchall()
    return [_model_row_to_read(row) for row in rows]


def get_model(connection: Connection, model_id: str) -> ModelConfigRead | None:
    row = connection.execute(f"{MODEL_SELECT_SQL} WHERE m.id = ?", (model_id,)).fetchone()
    return _model_row_to_read(row) if row else None


def _ensure_provider_exists(connection: Connection, provider_id: str) -> None:
    if connection.execute("SELECT 1 FROM model_providers WHERE id = ?", (provider_id,)).fetchone() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="provider not found")


def _clear_other_default_text_models(connection: Connection, model_id: str) -> None:
    connection.execute("UPDATE model_configs SET is_default_text_model = 0 WHERE id != ?", (model_id,))


def create_model(connection: Connection, payload: ModelConfigCreate) -> ModelConfigRead:
    _ensure_provider_exists(connection, payload.provider_id)
    model_id = f"model_{uuid4().hex}"
    now = _now_iso()
    if payload.is_default_text_model:
        _clear_other_default_text_models(connection, model_id)
    connection.execute(
        """
        INSERT INTO model_configs (
            id, provider_id, display_name, model_name, model_types_json, capability_tags_json,
            context_window, output_window, enabled, is_default_text_model, last_test_status, last_test_message,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)
        """,
        (
            model_id,
            payload.provider_id,
            payload.display_name.strip(),
            payload.model_name.strip(),
            _json_dumps_list(payload.model_types_json),
            _json_dumps_list(payload.capability_tags_json),
            payload.context_window,
            payload.output_window,
            1 if payload.enabled else 0,
            1 if payload.is_default_text_model else 0,
            now,
            now,
        ),
    )
    if payload.is_default_text_model:
        patch_route(connection, "default_text", ModelRouteUpdate(model_id=model_id))
    model = get_model(connection, model_id)
    if model is None:
        raise HTTPException(status_code=500, detail="failed to create model")
    return model


def update_model(connection: Connection, model_id: str, payload: ModelConfigUpdate) -> ModelConfigRead:
    existing = connection.execute("SELECT * FROM model_configs WHERE id = ?", (model_id,)).fetchone()
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="model not found")
    fields_set = getattr(payload, "model_fields_set", getattr(payload, "__fields_set__", set()))
    provider_id = payload.provider_id if payload.provider_id is not None else existing["provider_id"]
    _ensure_provider_exists(connection, provider_id)
    is_default = payload.is_default_text_model if payload.is_default_text_model is not None else _bool(existing["is_default_text_model"])
    if is_default:
        _clear_other_default_text_models(connection, model_id)
    connection.execute(
        """
        UPDATE model_configs
        SET provider_id = ?,
            display_name = ?,
            model_name = ?,
            model_types_json = ?,
            capability_tags_json = ?,
            context_window = ?,
            output_window = ?,
            enabled = ?,
            is_default_text_model = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            provider_id,
            payload.display_name.strip() if payload.display_name is not None else existing["display_name"],
            payload.model_name.strip() if payload.model_name is not None else existing["model_name"],
            _json_dumps_list(payload.model_types_json) if payload.model_types_json is not None else existing["model_types_json"],
            _json_dumps_list(payload.capability_tags_json) if payload.capability_tags_json is not None else existing["capability_tags_json"],
            payload.context_window if "context_window" in fields_set else existing["context_window"],
            payload.output_window if "output_window" in fields_set else existing["output_window"],
            1 if (payload.enabled if payload.enabled is not None else _bool(existing["enabled"])) else 0,
            1 if is_default else 0,
            _now_iso(),
            model_id,
        ),
    )
    if is_default:
        patch_route(connection, "default_text", ModelRouteUpdate(model_id=model_id))
    model = get_model(connection, model_id)
    if model is None:
        raise HTTPException(status_code=500, detail="failed to update model")
    return model


def delete_model(connection: Connection, model_id: str) -> bool:
    cursor = connection.execute("DELETE FROM model_configs WHERE id = ?", (model_id,))
    return cursor.rowcount > 0


def set_model_test_status(connection: Connection, model_id: str, status_value: str, message: str) -> None:
    connection.execute(
        "UPDATE model_configs SET last_test_status = ?, last_test_message = ?, updated_at = ? WHERE id = ?",
        (status_value, message[:2000], _now_iso(), model_id),
    )


def list_scenarios() -> list[ModelScenarioRead]:
    return [
        ModelScenarioRead(
            scenario=definition["scenario"],
            required_tags_json=list(definition["required_tags"]),
            is_required=bool(definition["is_required"]),
            fallback_scenario=definition["fallback_scenario"],
            description=SCENARIO_DESCRIPTIONS.get(definition["scenario"], ""),
        )
        for definition in MODEL_SCENARIO_DEFINITIONS
    ]


def list_routes(connection: Connection) -> list[ModelRouteRead]:
    rows = connection.execute(f"{ROUTE_SELECT_SQL} ORDER BY r.created_at ASC").fetchall()
    return [_route_row_to_read(row) for row in rows]


def get_route(connection: Connection, scenario: str) -> ModelRouteRead | None:
    row = connection.execute(f"{ROUTE_SELECT_SQL} WHERE r.scenario = ?", (scenario,)).fetchone()
    return _route_row_to_read(row) if row else None


def patch_route(connection: Connection, scenario: str, payload: ModelRouteUpdate) -> ModelRouteRead:
    existing = connection.execute("SELECT * FROM model_route_configs WHERE scenario = ?", (scenario,)).fetchone()
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="scenario route not found")
    fields_set = payload.model_fields_set
    next_model_id = payload.model_id if "model_id" in fields_set else existing["model_id"]
    next_fallback_scenario = payload.fallback_scenario if "fallback_scenario" in fields_set else existing["fallback_scenario"]
    if next_model_id:
        if connection.execute("SELECT 1 FROM model_configs WHERE id = ?", (next_model_id,)).fetchone() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="model not found")
    connection.execute(
        """
        UPDATE model_route_configs
        SET model_id = ?,
            required_tags_json = ?,
            is_required = ?,
            fallback_scenario = ?,
            enabled = ?,
            updated_at = ?
        WHERE scenario = ?
        """,
        (
            next_model_id,
            _json_dumps_list(payload.required_tags_json) if "required_tags_json" in fields_set else existing["required_tags_json"],
            1 if (payload.is_required if "is_required" in fields_set else _bool(existing["is_required"])) else 0,
            next_fallback_scenario,
            1 if (payload.enabled if "enabled" in fields_set else _bool(existing["enabled"])) else 0,
            _now_iso(),
            scenario,
        ),
    )
    route = get_route(connection, scenario)
    if route is None:
        raise HTTPException(status_code=500, detail="failed to update route")
    return route


def _model_candidate(connection: Connection, model_id: str) -> Row | None:
    return connection.execute(
        """
        SELECT
            m.id AS model_id,
            m.display_name,
            m.model_name,
            m.enabled AS model_enabled,
            p.id AS provider_id,
            p.name AS provider_name,
            p.provider_type,
            p.base_url,
            p.api_key_env_name,
            p.api_key,
            p.enabled AS provider_enabled
        FROM model_configs m
        JOIN model_providers p ON p.id = m.provider_id
        WHERE m.id = ?
        """,
        (model_id,),
    ).fetchone()


def _resolved_from_candidate(row: Row, scenario: str, source: str, route_chain: list[str]) -> ResolvedModel:
    if not _bool(row["model_enabled"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"model is disabled: {row['model_id']}")
    if not _bool(row["provider_enabled"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"provider is disabled: {row['provider_id']}")
    api_key = _resolve_api_key(row)
    if not api_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"API key is not configured for provider {row['provider_id']}")
    return ResolvedModel(
        scenario=scenario,
        provider_id=row["provider_id"],
        model_id=row["model_id"],
        provider_type=row["provider_type"],
        base_url=row["base_url"],
        api_key=api_key,
        model_name=row["model_name"],
        display_name=row["display_name"],
        source=source,
        route_chain=route_chain,
    )


def _default_text_candidate(connection: Connection) -> Row | None:
    return connection.execute(
        """
        SELECT
            m.id AS model_id,
            m.display_name,
            m.model_name,
            m.enabled AS model_enabled,
            p.id AS provider_id,
            p.name AS provider_name,
            p.provider_type,
            p.base_url,
            p.api_key_env_name,
            p.api_key,
            p.enabled AS provider_enabled
        FROM model_configs m
        JOIN model_providers p ON p.id = m.provider_id
        WHERE m.is_default_text_model = 1
        ORDER BY m.updated_at DESC
        LIMIT 1
        """
    ).fetchone()


def resolve_model_for_scenario(connection: Connection, scenario: str) -> ResolvedModel:
    current = scenario
    route_chain: list[str] = []
    visited: set[str] = set()
    while current and current not in visited:
        visited.add(current)
        route_chain.append(current)
        route = connection.execute("SELECT * FROM model_route_configs WHERE scenario = ? AND enabled = 1", (current,)).fetchone()
        if route is not None and route["model_id"]:
            candidate = _model_candidate(connection, route["model_id"])
            if candidate is not None:
                return _resolved_from_candidate(candidate, scenario, "route", route_chain)
        current = route["fallback_scenario"] if route is not None else None

    candidate = _default_text_candidate(connection)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No model configured for scenario and no default_text model is configured",
        )
    return _resolved_from_candidate(candidate, scenario, "default_text", route_chain or [scenario])


def resolve_model_by_id(connection: Connection, model_id: str, scenario: str = "default_text") -> ResolvedModel:
    candidate = _model_candidate(connection, model_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="model not found")
    return _resolved_from_candidate(candidate, scenario, "model_test", [scenario])
