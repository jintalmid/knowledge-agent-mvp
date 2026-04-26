from fastapi import APIRouter

from app.db.sqlite import db_session
from app.schemas.excel import ExcelAnalyzeRequest, ExcelAnalyzeResponse
from app.services import excel_analysis as excel_analysis_service

router = APIRouter(tags=["excel-analysis"])


@router.post("/task-files/{task_file_id}/excel/analyze", response_model=ExcelAnalyzeResponse)
def analyze_excel_task_file(task_file_id: str, payload: ExcelAnalyzeRequest) -> ExcelAnalyzeResponse:
    with db_session() as connection:
        return excel_analysis_service.analyze_excel_task_file(
            connection,
            task_file_id=task_file_id,
            question=payload.question,
            sheet_name=payload.sheet_name,
            agent_run_id=payload.agent_run_id,
            iteration_id=payload.iteration_id,
        )
