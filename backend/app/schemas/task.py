from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskStatus


class TaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    knowledge_base_id: str | None = Field(default=None, max_length=120)
    template_id: str | None = Field(default=None, max_length=120)


class TaskUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus | None = None
    knowledge_base_id: str | None = Field(default=None, max_length=120)
    template_id: str | None = Field(default=None, max_length=120)
    iteration_count: int | None = Field(default=None, ge=0)


class TaskRead(BaseModel):
    id: str
    name: str
    description: str
    status: TaskStatus
    owner_user_id: str
    department_id: str
    security_level: str
    knowledge_base_id: str | None
    template_id: str | None
    iteration_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
