from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "knowledge-agent-mvp"
    api_prefix: str = "/api"
    registry_path: Path = Path(__file__).resolve().parents[3] / "module-registry.json"
    uploads_dir: Path = Path(__file__).resolve().parents[2] / "uploads"
    sqlite_path: Path = Path(__file__).resolve().parents[2] / "knowledge_agent_mvp.sqlite3"

    llm_provider_type: str | None = None
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
