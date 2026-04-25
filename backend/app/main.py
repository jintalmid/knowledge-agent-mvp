from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.files import router as files_router
from app.api.routes import router
from app.api.tasks import router as tasks_router
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


@app.on_event("startup")
def startup() -> None:
    init_db()
