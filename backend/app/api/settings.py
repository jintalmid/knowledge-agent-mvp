from fastapi import APIRouter

from app.db.sqlite import db_session
from app.schemas.llm import LlmSettingsRead, LlmTestRead
from app.services import llm as llm_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/llm", response_model=LlmSettingsRead)
def get_llm_settings() -> LlmSettingsRead:
    return llm_service.get_llm_settings()


@router.post("/llm/test", response_model=LlmTestRead)
def test_llm() -> LlmTestRead:
    with db_session() as connection:
        result = llm_service.call_llm(
            connection,
            task_id=None,
            scenario="default_text",
            module_name="M13_LLM_CALL_LOGGING",
            system_prompt="You are a health-check assistant. Reply briefly.",
            user_prompt="Return the word ok and a short confirmation.",
        )
        return LlmTestRead(status="success", response_preview=result.text[:500], log_id=result.log_id)
