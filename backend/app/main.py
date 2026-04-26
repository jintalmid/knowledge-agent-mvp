from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agent_runner import router as agent_runner_router
from app.api.capability import router as capability_router
from app.api.excel_analysis import router as excel_analysis_router
from app.api.files import router as files_router
from app.api.llm_logs import router as llm_logs_router
from app.api.parsing import router as parsing_router
from app.api.qa import router as qa_router
from app.api.retrieval import router as retrieval_router
from app.api.routes import router
from app.api.settings import router as settings_router
from app.api.summaries import router as summaries_router
from app.api.tasks import router as tasks_router
from app.api.tools import router as tools_router
from app.core.config import get_settings
from app.db.sqlite import init_db

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_prefix)
app.include_router(tasks_router, prefix=settings.api_prefix)
app.include_router(files_router, prefix=settings.api_prefix)
app.include_router(parsing_router, prefix=settings.api_prefix)
app.include_router(summaries_router, prefix=settings.api_prefix)
app.include_router(settings_router, prefix=settings.api_prefix)
app.include_router(llm_logs_router, prefix=settings.api_prefix)
app.include_router(retrieval_router, prefix=settings.api_prefix)
app.include_router(qa_router, prefix=settings.api_prefix)
app.include_router(excel_analysis_router, prefix=settings.api_prefix)
app.include_router(capability_router, prefix=settings.api_prefix)
app.include_router(tools_router, prefix=settings.api_prefix)
app.include_router(agent_runner_router, prefix=settings.api_prefix)


@app.on_event("startup")
def startup() -> None:
    init_db()
