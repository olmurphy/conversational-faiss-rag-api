from api.schemas.status_ok_schema import StatusOkResponseSchema
from fastapi import APIRouter, status

router = APIRouter()


@router.get(
    "/readiness",
    response_model=StatusOkResponseSchema,
    status_code=status.HTTP_200_OK,
    tags=["Health"],
)
async def readiness():
    """
    This route is used as a readinessProbe for Kubernetes. By default, the
    route will always response with an OK status and the 200 HTTP code as soon
    as the service is up.
    """
    return {"statusOk": True}
