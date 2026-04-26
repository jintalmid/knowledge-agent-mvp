from fastapi import APIRouter, HTTPException

from app.db.sqlite import db_session
from app.schemas.agent_runner import AgentRunCreate, AgentRunRead, AgentRunStartResponse
from app.services import agent_runner as agent_runner_service

router = APIRouter(tags=["agent-runner"])


@router.post("/tasks/{task_id}/agent-runs", response_model=AgentRunStartResponse)
def start_agent_run(task_id: str, payload: AgentRunCreate) -> AgentRunStartResponse:
    with db_session() as connection:
        return agent_runner_service.start_agent_run(
            connection,
            task_id=task_id,
            question=payload.question,
            max_iterations=payload.max_iterations,
        )


@router.get("/agent-runs/{run_id}", response_model=AgentRunRead)
def get_agent_run(run_id: str) -> AgentRunRead:
    with db_session() as connection:
        agent_run = agent_runner_service.get_agent_run(connection, run_id)
        if agent_run is None:
            raise HTTPException(status_code=404, detail="agent run not found")
        return agent_run
