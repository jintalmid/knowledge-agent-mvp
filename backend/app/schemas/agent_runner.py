from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentRunCreate(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    max_iterations: int = Field(default=10, ge=1, le=10)


class AgentRunStartResponse(BaseModel):
    agent_run_id: str
    answer_id: str | None
    status: str
    iteration_count: int


class ObservationRead(BaseModel):
    id: str
    agent_run_id: str
    agent_iteration_id: str
    tool_name: str
    observation_type: str
    content_text: str | None
    content_json: dict[str, Any] | None
    status: str
    error_message: str | None
    created_at: datetime


class AgentIterationRead(BaseModel):
    id: str
    agent_run_id: str
    iteration_index: int
    plan_text: dict[str, Any] | None
    tool_name: str | None
    tool_input_json: dict[str, Any] | None
    tool_result_json: dict[str, Any] | None
    reflection_text: dict[str, Any] | None
    decision: str
    llm_call_log_id: str | None
    status: str
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
    observations: list[ObservationRead] = []


class AgentRunRead(BaseModel):
    id: str
    task_id: str | None
    answer_id: str | None = None
    goal: str
    status: str
    max_iterations: int
    current_iteration: int
    final_answer_markdown: str | None
    stop_reason: str | None
    owner_user_id: str
    department_id: str
    security_level: str
    created_at: datetime
    updated_at: datetime
    iterations: list[AgentIterationRead] = []
