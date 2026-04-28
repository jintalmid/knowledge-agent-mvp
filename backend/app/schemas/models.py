from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ModelProviderCreate(BaseModel):
    name: str
    provider_type: str = "openai_compatible"
    base_url: str
    api_key_env_name: str | None = None
    api_key: str | None = None
    enabled: bool = True


class ModelProviderUpdate(BaseModel):
    name: str | None = None
    provider_type: str | None = None
    base_url: str | None = None
    api_key_env_name: str | None = None
    api_key: str | None = None
    enabled: bool | None = None


class ModelProviderRead(BaseModel):
    id: str
    name: str
    provider_type: str
    base_url: str
    api_key_env_name: str | None
    api_key_configured: bool
    enabled: bool
    created_at: datetime
    updated_at: datetime


class ModelConfigCreate(BaseModel):
    provider_id: str
    display_name: str
    model_name: str
    model_types_json: list[str] = Field(default_factory=lambda: ["text"])
    capability_tags_json: list[str] = Field(default_factory=lambda: ["text"])
    context_window: int | None = None
    output_window: int | None = None
    enabled: bool = True
    is_default_text_model: bool = False


class ModelConfigUpdate(BaseModel):
    provider_id: str | None = None
    display_name: str | None = None
    model_name: str | None = None
    model_types_json: list[str] | None = None
    capability_tags_json: list[str] | None = None
    context_window: int | None = None
    output_window: int | None = None
    enabled: bool | None = None
    is_default_text_model: bool | None = None


class ModelConfigRead(BaseModel):
    id: str
    provider_id: str
    provider_name: str | None = None
    provider_type: str | None = None
    display_name: str
    model_name: str
    model_types_json: list[str]
    capability_tags_json: list[str]
    context_window: int | None
    output_window: int | None
    enabled: bool
    is_default_text_model: bool
    last_test_status: str | None
    last_test_message: str | None
    created_at: datetime
    updated_at: datetime


class ModelTestRead(BaseModel):
    status: str
    message: str
    response_preview: str | None = None
    log_id: str | None = None


class ModelScenarioRead(BaseModel):
    scenario: str
    required_tags_json: list[str]
    is_required: bool
    fallback_scenario: str | None
    description: str


class ModelRouteUpdate(BaseModel):
    model_id: str | None = None
    required_tags_json: list[str] | None = None
    is_required: bool | None = None
    fallback_scenario: str | None = None
    enabled: bool | None = None


class ModelRouteRead(BaseModel):
    id: str
    scenario: str
    model_id: str | None
    model_display_name: str | None = None
    model_name: str | None = None
    provider_id: str | None = None
    provider_name: str | None = None
    required_tags_json: list[str]
    is_required: bool
    fallback_scenario: str | None
    enabled: bool
    health_status: str
    health_message: str
    created_at: datetime
    updated_at: datetime


class ModelRouteTestRead(BaseModel):
    scenario: str
    resolved_model_id: str | None
    resolved_provider_id: str | None
    status: str
    message: str
    response_preview: str | None = None
    log_id: str | None = None


class ResolvedModelContext(BaseModel):
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


JsonDict = dict[str, Any]
