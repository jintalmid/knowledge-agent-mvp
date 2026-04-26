from typing import Any

from pydantic import BaseModel, Field


class ToolRead(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    safety_notes: list[str]


class ToolCallRequest(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)


class ToolCallResponse(BaseModel):
    tool_name: str
    status: str
    output: dict[str, Any]
