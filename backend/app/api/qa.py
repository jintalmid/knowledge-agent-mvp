from fastapi import APIRouter, HTTPException

from app.db.sqlite import db_session
from app.schemas.qa import AnswerRead, AskRequest
from app.services import qa as qa_service

router = APIRouter(tags=["qa"])


@router.post("/tasks/{task_id}/ask", response_model=AnswerRead)
def ask_task_question(task_id: str, payload: AskRequest) -> AnswerRead:
    with db_session() as connection:
        return qa_service.ask_task_question(connection, task_id, payload.question_text)


@router.get("/tasks/{task_id}/results", response_model=list[AnswerRead])
def list_task_results(task_id: str) -> list[AnswerRead]:
    with db_session() as connection:
        results = qa_service.list_task_results(connection, task_id)
        if results is None:
            raise HTTPException(status_code=404, detail="task not found")
        return results


@router.get("/answers/{answer_id}", response_model=AnswerRead)
def get_answer(answer_id: str) -> AnswerRead:
    with db_session() as connection:
        answer = qa_service.get_answer(connection, answer_id)
        if answer is None:
            raise HTTPException(status_code=404, detail="answer not found")
        return answer
