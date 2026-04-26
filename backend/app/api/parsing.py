from fastapi import APIRouter, HTTPException

from app.db.sqlite import db_session
from app.schemas.parsing import ParsedContentRead
from app.services import parsing as parsing_service

router = APIRouter(tags=["parsing"])


@router.post("/task-files/{task_file_id}/parse", response_model=ParsedContentRead)
def parse_task_file(task_file_id: str) -> ParsedContentRead:
    with db_session() as connection:
        return parsing_service.parse_task_file(connection, task_file_id)


@router.post("/tasks/{task_id}/parse-all", response_model=list[ParsedContentRead])
def parse_all_task_files(task_id: str) -> list[ParsedContentRead]:
    with db_session() as connection:
        return parsing_service.parse_all_task_files(connection, task_id)


@router.get("/task-files/{task_file_id}/parsed-content", response_model=ParsedContentRead)
def get_parsed_content(task_file_id: str) -> ParsedContentRead:
    with db_session() as connection:
        parsed_content = parsing_service.get_parsed_content(connection, task_file_id)
        if parsed_content is None:
            raise HTTPException(status_code=404, detail="parsed content not found")
        return parsed_content
