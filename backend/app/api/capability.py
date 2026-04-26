from fastapi import APIRouter

from app.db.sqlite import db_session
from app.schemas.capability import CapabilityCheckRead, Phase0RequirementsRead
from app.services import capability as capability_service

router = APIRouter(tags=["capability"])


@router.get("/tasks/{task_id}/capability-check", response_model=CapabilityCheckRead)
def get_task_capability_check(task_id: str) -> CapabilityCheckRead:
    with db_session() as connection:
        return capability_service.check_task_capability(connection, task_id)


@router.get("/phase0/requirements", response_model=Phase0RequirementsRead)
def get_phase0_requirements() -> Phase0RequirementsRead:
    return capability_service.get_phase0_requirements()
