import uuid

from fastapi import APIRouter, Request, status

from context import AppContext
from api.controllers.helper import format_response
from api.schemas.user_interactions_schema import UpdateInteractionInputSchema, UpdateInteractionOutputSchema
from application.user_interactions.service import UserInteractionService

router = APIRouter()

@router.put(
    "/interactions/{interaction_id}",
    responses={
        200: {"model": UpdateInteractionOutputSchema, "description": "Interaction updated successfully"},
        400: {"description": "Invalid input"},
        404: {"description": "Interaction not found"},
        500: {"description": "Internal server error"},
    },
    status_code=status.HTTP_200_OK,
    tags=["user-interaction"],
)
async def update_interaction_handler(
    interaction_id: uuid.UUID,
    request: Request,
    update_data: UpdateInteractionInputSchema,
):
    """
    Updates a user interaction record with feedback and rating.
    """
    request_context: AppContext = request.state.app_context
    logger = request_context.logger
    logger.info({
        "message": "Received request to update interaction",
        "data": {
            "interaction_id": str(interaction_id),
            "update_data": str(update_data)
        }
    })
    user_interactions_service = UserInteractionService(app_context=request_context)
    await user_interactions_service.record_user_feedback(interaction_id, update_data)
    

    return format_response(
        status=status.HTTP_200_OK,
        message="Success",
    )
