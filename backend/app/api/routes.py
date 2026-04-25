import json

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": get_settings().app_name}


@router.get("/modules")
def list_modules() -> list[dict]:
    registry_path = get_settings().registry_path
    if not registry_path.exists():
        raise HTTPException(status_code=500, detail="module registry not found")

    with registry_path.open("r", encoding="utf-8") as registry_file:
        return json.load(registry_file)
