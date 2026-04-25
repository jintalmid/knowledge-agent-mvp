from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from app.core.auth import CurrentUser, get_current_user
from app.db.sqlite import db_session
from app.schemas.file import PhysicalFileRead, TaskFileRead
from app.services import files as file_service

router = APIRouter(tags=["files"])


@router.post("/tasks/{task_id}/files", response_model=TaskFileRead, status_code=status.HTTP_201_CREATED)
async def upload_task_file(
    task_id: str,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskFileRead:
    with db_session() as connection:
        return await file_service.create_task_file(connection, task_id, file, current_user)


@router.get("/tasks/{task_id}/files", response_model=list[TaskFileRead])
def list_task_files(task_id: str) -> list[TaskFileRead]:
    with db_session() as connection:
        task_files = file_service.list_task_files(connection, task_id)
        if task_files is None:
            raise HTTPException(status_code=404, detail="task not found")
        return task_files


@router.get("/task-files/{task_file_id}", response_model=TaskFileRead)
def get_task_file(task_file_id: str) -> TaskFileRead:
    with db_session() as connection:
        task_file = file_service.get_task_file(connection, task_file_id)
        if task_file is None:
            raise HTTPException(status_code=404, detail="task file not found")
        return task_file


@router.delete("/task-files/{task_file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_file(task_file_id: str) -> Response:
    with db_session() as connection:
        deleted = file_service.delete_task_file(connection, task_file_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="task file not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/physical-files/{physical_file_id}", response_model=PhysicalFileRead)
def get_physical_file(physical_file_id: str) -> PhysicalFileRead:
    with db_session() as connection:
        physical_file = file_service.get_physical_file(connection, physical_file_id)
        if physical_file is None:
            raise HTTPException(status_code=404, detail="physical file not found")
        return physical_file
