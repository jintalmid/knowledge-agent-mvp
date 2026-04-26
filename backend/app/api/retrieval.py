from fastapi import APIRouter

from app.db.sqlite import db_session
from app.schemas.retrieval import (
    DocumentChunkRead,
    RetrievalSettingsRead,
    RetrievalSettingsUpdate,
    RetrieveRequest,
    RetrieveResponse,
)
from app.services import retrieval as retrieval_service

router = APIRouter(tags=["retrieval"])


@router.post("/task-files/{task_file_id}/chunks", response_model=list[DocumentChunkRead])
def generate_task_file_chunks(task_file_id: str) -> list[DocumentChunkRead]:
    with db_session() as connection:
        return retrieval_service.generate_task_file_chunks(connection, task_file_id)


@router.get("/task-files/{task_file_id}/chunks", response_model=list[DocumentChunkRead])
def list_task_file_chunks(task_file_id: str) -> list[DocumentChunkRead]:
    with db_session() as connection:
        return retrieval_service.list_task_file_chunks(connection, task_file_id)


@router.get("/settings/retrieval", response_model=RetrievalSettingsRead)
def get_retrieval_settings() -> RetrievalSettingsRead:
    with db_session() as connection:
        return retrieval_service.get_retrieval_settings(connection)


@router.patch("/settings/retrieval", response_model=RetrievalSettingsRead)
def update_retrieval_settings(payload: RetrievalSettingsUpdate) -> RetrievalSettingsRead:
    with db_session() as connection:
        return retrieval_service.update_retrieval_settings(connection, payload)


@router.post("/tasks/{task_id}/retrieve", response_model=RetrieveResponse)
def retrieve_task_files(task_id: str, payload: RetrieveRequest) -> RetrieveResponse:
    with db_session() as connection:
        return retrieval_service.retrieve_task_files(
            connection,
            task_id=task_id,
            question=payload.question,
            retrieval_mode=payload.retrieval_mode,
            top_k=payload.top_k,
        )
