import enum
from typing import List, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field, conint, field_validator
from fastapi import APIRouter, Request, status

from api.schemas.base_request_response_model import BaseResponse
from models.user_interactions import InteractionResultType


class UpdateInteractionInputSchema(BaseModel):
    interaction_result: Optional[InteractionResultType] = Field(
        None, description="The result of the interaction (positive, negative, etc.)"
    )
    feedback_reason: Optional[str] = Field(None, description="Reason for the feedback")
    rating: Optional[int] = Field(
        None, description="Rating of the interaction (1-5)"
    )
    interaction_time: Optional[int] = Field(
        None, description="Time spent on the interaction"
    )
    clicks: Optional[int] = Field(None, description="Number of clicks")
    scroll_depth: Optional[float] = Field(None, description="Scroll depth")

    @field_validator("rating")
    def validate_rating(cls, value):
        if value is not None and (not 1 <= value <= 5):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rating must be between 1 and 5"
            )
        return value
    
    @field_validator("interaction_result")
    def validate_interaction_result(cls, value):
        if value is not None and not isinstance(value, InteractionResultType):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid interaction result type"
            )
        return value
    

UpdateInteractionOutputSchema = BaseResponse[None]