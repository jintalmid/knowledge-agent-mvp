from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ParsedContentRead(BaseModel):
    id: str
    task_file_id: str
    physical_file_id: str
    content_type: str
    text_content: str | None
    excel_profile_json: dict[str, Any] | None
    parse_quality: str
    created_at: datetime
    updated_at: datetime
