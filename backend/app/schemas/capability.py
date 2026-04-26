from typing import Literal

from pydantic import BaseModel

CapabilityStepStatus = Literal["passed", "missing", "failed"]
CapabilityOverallStatus = Literal["ready", "incomplete", "failed"]


class CapabilityStepRead(BaseModel):
    step: str
    status: CapabilityStepStatus
    message: str
    next_page: str | None


class CapabilityCheckRead(BaseModel):
    task_id: str
    phase: str
    steps: list[CapabilityStepRead]
    overall_status: CapabilityOverallStatus


class Phase0RequirementRead(BaseModel):
    step: str
    description: str
    module_ids: list[str]
    recommended_page: str


class Phase0RequirementsRead(BaseModel):
    phase: str
    requirements: list[Phase0RequirementRead]
