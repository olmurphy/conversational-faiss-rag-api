from context import AppContext
from fastapi import APIRouter, Request, status

router = APIRouter()


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def metrics(request: Request):
    app_context: AppContext = request.state.app_context

    metrics_manager = app_context.metrics_manager

    return metrics_manager.expose_metrics()
