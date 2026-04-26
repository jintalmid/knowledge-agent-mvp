from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question_text: str = Field(min_length=1, max_length=4000)


class QuestionRead(BaseModel):
    id: str
    task_id: str
    question_text: str
    question_type: str
    created_at: datetime


class SourceRefRead(BaseModel):
    task_file_id: str
    physical_file_id: str
    display_name: str
    score: float
    matched_fields: list[str]
    reason: str
    content_type: str
    chunk_refs: list[dict[str, Any]] = []


class AnswerRead(BaseModel):
    id: str
    task_id: str
    agent_run_id: str | None = None
    question_id: str
    question_text: str
    question_type: str
    answer_text_markdown: str
    selected_task_file_ids_json: list[str]
    source_refs_json: list[SourceRefRead]
    iteration_count: int
    llm_provider: str
    llm_model: str
    created_at: datetime
