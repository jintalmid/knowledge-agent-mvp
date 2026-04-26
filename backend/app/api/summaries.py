from fastapi import APIRouter, HTTPException

from app.db.sqlite import db_session
from app.schemas.summary import FileSummaryRead
from app.services import summaries as summary_service

router = APIRouter(tags=["summaries"])


@router.post("/task-files/{task_file_id}/summarize", response_model=FileSummaryRead)
def summarize_task_file(task_file_id: str) -> FileSummaryRead:
    with db_session() as connection:
        return summary_service.summarize_task_file(connection, task_file_id)


@router.post("/tasks/{task_id}/summarize-all", response_model=list[FileSummaryRead])
def summarize_all_task_files(task_id: str) -> list[FileSummaryRead]:
    with db_session() as connection:
        return summary_service.summarize_all_task_files(connection, task_id)


@router.get("/tasks/{task_id}/summaries", response_model=list[FileSummaryRead])
def list_task_summaries(task_id: str) -> list[FileSummaryRead]:
    with db_session() as connection:
        summaries = summary_service.list_task_summaries(connection, task_id)
        if summaries is None:
            raise HTTPException(status_code=404, detail="task not found")
        return summaries


@router.get("/task-files/{task_file_id}/summary", response_model=FileSummaryRead)
def get_task_file_summary(task_file_id: str) -> FileSummaryRead:
    with db_session() as connection:
        summary = summary_service.get_task_file_summary(connection, task_file_id)
        if summary is None:
            raise HTTPException(status_code=404, detail="summary not found")
        return summary
