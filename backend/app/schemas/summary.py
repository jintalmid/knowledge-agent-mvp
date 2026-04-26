from datetime import datetime
from typing import Any

from pydantic import BaseModel


class FileSummaryRead(BaseModel):
    id: str
    task_file_id: str
    physical_file_id: str
    summary_text: str
    keywords_json: list[str]
    tags_json: list[str]
    category: str
    summary_method: str
    llm_provider: str
    llm_model: str
    knowledge_item_id: str | None
    table_understanding: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
