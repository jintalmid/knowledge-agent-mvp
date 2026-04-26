from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

RetrievalMode = Literal["summary_only", "chunk_text", "embedding", "hybrid"]


class DocumentChunkRead(BaseModel):
    id: str
    task_file_id: str
    physical_file_id: str
    chunk_index: int
    content: str
    metadata_json: dict[str, Any]
    created_at: datetime


class RetrievalSettingsRead(BaseModel):
    retrieval_mode: RetrievalMode
    chunk_size: int
    chunk_overlap: int
    top_k: int
    embedding_provider: str | None
    embedding_model: str | None
    vector_store: str | None
    updated_at: datetime


class RetrievalSettingsUpdate(BaseModel):
    retrieval_mode: RetrievalMode | None = None
    chunk_size: int | None = Field(default=None, ge=200, le=12000)
    chunk_overlap: int | None = Field(default=None, ge=0, le=4000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    embedding_provider: str | None = None
    embedding_model: str | None = None
    vector_store: str | None = None


class RetrieveRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    retrieval_mode: RetrievalMode | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)


class ChunkMatchRead(BaseModel):
    chunk_id: str
    chunk_index: int
    score: float
    preview: str


class RetrievalCandidateRead(BaseModel):
    task_file_id: str
    physical_file_id: str
    display_name: str
    score: float
    matched_fields: list[str]
    reason: str
    chunk_matches: list[ChunkMatchRead] = []


class RetrieveResponse(BaseModel):
    retrieval_mode: RetrievalMode
    status: str
    message: str
    results: list[RetrievalCandidateRead]
