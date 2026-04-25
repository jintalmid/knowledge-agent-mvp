from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.auth import CurrentUser, get_current_user
from app.db.sqlite import db_session
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services import tasks as task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskRead:
    with db_session() as connection:
        task = task_service.create_task(connection, payload, current_user)
        if task is None:
            raise HTTPException(status_code=500, detail="failed to create task")
        return task


@router.get("", response_model=list[TaskRead])
def list_tasks() -> list[TaskRead]:
    with db_session() as connection:
        return task_service.list_tasks(connection)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: str) -> TaskRead:
    with db_session() as connection:
        task = task_service.get_task(connection, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="task not found")
        return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: str, payload: TaskUpdate) -> TaskRead:
    with db_session() as connection:
        task = task_service.update_task(connection, task_id, payload)
        if task is None:
            raise HTTPException(status_code=404, detail="task not found")
        return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str) -> Response:
    with db_session() as connection:
        deleted = task_service.delete_task(connection, task_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
