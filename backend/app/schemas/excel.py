from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.qa import AnswerRead


class ExcelAnalyzeRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    sheet_name: str | None = Field(default=None, max_length=200)
    agent_run_id: str | None = None
    iteration_id: str | None = None


class ExcelAnalysisRunRead(BaseModel):
    id: str
    task_id: str
    agent_run_id: str | None = None
    iteration_id: str | None = None
    task_file_id: str
    question_id: str
    generated_code: str
    final_code: str
    code_status: str
    execution_status: str
    result_json: dict[str, Any] | list[Any] | None
    stdout: str | None
    stderr: str | None
    repair_attempts: int
    first_error: str | None
    created_at: datetime
    updated_at: datetime


class ExcelAnalyzeResponse(BaseModel):
    run: ExcelAnalysisRunRead
    answer: AnswerRead | None
