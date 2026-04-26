from fastapi import APIRouter

from app.db.sqlite import db_session
from app.schemas.tools import ToolCallRequest, ToolCallResponse, ToolRead
from app.services import tool_registry

router = APIRouter(tags=["tools"])


@router.get("/tools", response_model=list[ToolRead])
def list_tools() -> list[ToolRead]:
    return tool_registry.list_tools()


@router.post("/tools/{tool_name}/call", response_model=ToolCallResponse)
def call_tool(tool_name: str, payload: ToolCallRequest) -> ToolCallResponse:
    with db_session() as connection:
        return tool_registry.call_tool(connection, tool_name, payload.input)
