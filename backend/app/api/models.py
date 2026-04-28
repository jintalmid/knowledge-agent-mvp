from fastapi import APIRouter, HTTPException, Response

from app.db.sqlite import db_session
from app.schemas.models import (
    ModelConfigCreate,
    ModelConfigRead,
    ModelConfigUpdate,
    ModelProviderCreate,
    ModelProviderRead,
    ModelProviderUpdate,
    ModelRouteRead,
    ModelRouteTestRead,
    ModelRouteUpdate,
    ModelScenarioRead,
    ModelTestRead,
)
from app.services import llm as llm_service
from app.services import model_registry

router = APIRouter(tags=["models"])


@router.get("/model-providers", response_model=list[ModelProviderRead])
def list_model_providers() -> list[ModelProviderRead]:
    with db_session() as connection:
        return model_registry.list_providers(connection)


@router.post("/model-providers", response_model=ModelProviderRead)
def create_model_provider(payload: ModelProviderCreate) -> ModelProviderRead:
    with db_session() as connection:
        return model_registry.create_provider(connection, payload)


@router.get("/model-providers/{provider_id}", response_model=ModelProviderRead)
def get_model_provider(provider_id: str) -> ModelProviderRead:
    with db_session() as connection:
        provider = model_registry.get_provider(connection, provider_id)
        if provider is None:
            raise HTTPException(status_code=404, detail="provider not found")
        return provider


@router.patch("/model-providers/{provider_id}", response_model=ModelProviderRead)
def update_model_provider(provider_id: str, payload: ModelProviderUpdate) -> ModelProviderRead:
    with db_session() as connection:
        return model_registry.update_provider(connection, provider_id, payload)


@router.delete("/model-providers/{provider_id}", status_code=204)
def delete_model_provider(provider_id: str) -> Response:
    with db_session() as connection:
        if not model_registry.delete_provider(connection, provider_id):
            raise HTTPException(status_code=404, detail="provider not found")
    return Response(status_code=204)


@router.get("/models", response_model=list[ModelConfigRead])
def list_models() -> list[ModelConfigRead]:
    with db_session() as connection:
        return model_registry.list_models(connection)


@router.post("/models", response_model=ModelConfigRead)
def create_model(payload: ModelConfigCreate) -> ModelConfigRead:
    with db_session() as connection:
        return model_registry.create_model(connection, payload)


@router.get("/models/{model_id}", response_model=ModelConfigRead)
def get_model(model_id: str) -> ModelConfigRead:
    with db_session() as connection:
        model = model_registry.get_model(connection, model_id)
        if model is None:
            raise HTTPException(status_code=404, detail="model not found")
        return model


@router.patch("/models/{model_id}", response_model=ModelConfigRead)
def update_model(model_id: str, payload: ModelConfigUpdate) -> ModelConfigRead:
    with db_session() as connection:
        return model_registry.update_model(connection, model_id, payload)


@router.delete("/models/{model_id}", status_code=204)
def delete_model(model_id: str) -> Response:
    with db_session() as connection:
        if not model_registry.delete_model(connection, model_id):
            raise HTTPException(status_code=404, detail="model not found")
    return Response(status_code=204)


@router.post("/models/{model_id}/test", response_model=ModelTestRead)
def test_model(model_id: str) -> ModelTestRead:
    with db_session() as connection:
        try:
            result = llm_service.call_llm(
                connection,
                task_id=None,
                scenario="default_text",
                model_id_override=model_id,
                module_name="M04_MODEL_REGISTRY_TEST",
                system_prompt="You are a model health-check assistant. Reply briefly.",
                user_prompt="Return the word ok and a short confirmation.",
            )
            model_registry.set_model_test_status(connection, model_id, "success", result.text[:500])
            return ModelTestRead(status="success", message="model test succeeded", response_preview=result.text[:500], log_id=result.log_id)
        except HTTPException as exc:
            model_registry.set_model_test_status(connection, model_id, "failed", str(exc.detail))
            connection.commit()
            raise


@router.get("/model-scenarios", response_model=list[ModelScenarioRead])
def list_model_scenarios() -> list[ModelScenarioRead]:
    return model_registry.list_scenarios()


@router.get("/model-routes", response_model=list[ModelRouteRead])
def list_model_routes() -> list[ModelRouteRead]:
    with db_session() as connection:
        return model_registry.list_routes(connection)


@router.patch("/model-routes/{scenario}", response_model=ModelRouteRead)
def update_model_route(scenario: str, payload: ModelRouteUpdate) -> ModelRouteRead:
    with db_session() as connection:
        return model_registry.patch_route(connection, scenario, payload)


@router.post("/model-routes/{scenario}/test", response_model=ModelRouteTestRead)
def test_model_route(scenario: str) -> ModelRouteTestRead:
    with db_session() as connection:
        resolved = model_registry.resolve_model_for_scenario(connection, scenario)
        result = llm_service.call_llm(
            connection,
            task_id=None,
            scenario=scenario,
            module_name="M04_MODEL_ROUTE_TEST",
            system_prompt="You are a model route health-check assistant. Reply briefly.",
            user_prompt=f"Return the word ok and confirm the scenario {scenario}.",
        )
        return ModelRouteTestRead(
            scenario=scenario,
            resolved_model_id=resolved.model_id,
            resolved_provider_id=resolved.provider_id,
            status="success",
            message="route test succeeded",
            response_preview=result.text[:500],
            log_id=result.log_id,
        )
