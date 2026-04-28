from datetime import datetime

from pydantic import BaseModel


class LlmSettingsRead(BaseModel):
    provider_type: str | None
    config_source: str
    env_file_path: str
    base_url: str | None
    base_url_configured: bool
    api_key_configured: bool
    model: str | None
    timeout_seconds: int
    ready: bool


class LlmTestRead(BaseModel):
    status: str
    response_preview: str
    log_id: str


class LlmCallLogRead(BaseModel):
    id: str
    task_id: str | None
    task_name: str | None = None
    owner_user_id: str | None = None
    department_id: str | None = None
    security_level: str | None = None
    agent_run_id: str | None = None
    iteration_id: str | None = None
    module_name: str
    provider_type: str
    model_name: str
    prompt_preview: str
    response_preview: str | None
    status: str
    error_message: str | None
    latency_ms: int
    created_at: datetime
