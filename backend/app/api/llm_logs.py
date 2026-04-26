from fastapi import APIRouter, HTTPException

from app.db.sqlite import db_session
from app.schemas.llm import LlmCallLogRead
from app.services import llm as llm_service

router = APIRouter(prefix="/llm-logs", tags=["llm-logs"])


@router.get("", response_model=list[LlmCallLogRead])
def list_llm_logs() -> list[LlmCallLogRead]:
    with db_session() as connection:
        return llm_service.list_logs(connection)


@router.get("/{log_id}", response_model=LlmCallLogRead)
def get_llm_log(log_id: str) -> LlmCallLogRead:
    with db_session() as connection:
        log = llm_service.get_log(connection, log_id)
        if log is None:
            raise HTTPException(status_code=404, detail="llm log not found")
        return log
