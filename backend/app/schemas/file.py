from datetime import datetime

from pydantic import BaseModel


class PhysicalFileRead(BaseModel):
    id: str
    content_hash: str
    original_filename: str
    file_ext: str
    mime_type: str
    file_size: int
    storage_path: str
    ref_count: int
    created_at: datetime
    updated_at: datetime


class TaskFileRead(BaseModel):
    id: str
    task_id: str
    physical_file_id: str
    display_name: str
    file_role: str
    parse_status: str
    parse_error: str | None = None
    summary_status: str
    embedding_status: str
    owner_user_id: str
    department_id: str
    security_level: str
    created_at: datetime
    updated_at: datetime
    file_ext: str
    mime_type: str
    file_size: int
    ref_count: int
    reused_existing_file: bool
