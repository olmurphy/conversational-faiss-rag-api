# pylint: disable=no-self-argument

from typing import List, Optional, Dict, Any  # Import Optional

from pydantic import BaseModel, field_validator, Field
from fastapi import HTTPException

from api.schemas.base_request_response_model import BaseResponse

class IdentifyIntentInputSchema(BaseModel):
    """
    Represents the input schema for chat completion.

    Attributes:
        chat_query (str): The current query in the chat.
        chat_history (List[str]): The history of the chat messages.
    """
    query: str

    @field_validator('query')
    def validate_chat_query_length(cls, query):
        max_length = 2000
        if len(query) > max_length:
            raise HTTPException(
                status_code=413,
                detail=f'query length exceeds {max_length} characters'
            )
        return query

class IdentifyIntentSchema(BaseModel):
    """
    Represents the output schema for chat completion.

    Attributes:
        text (str): The completed message based on the input chat query and history.
        input_documents (List[Document]): List of input documents provided for the completion.
    """
    Application: List[str]
    Entities: List[str]
    Follow_up: List[str]

IdentifyIntentOutputSchema = BaseResponse[IdentifyIntentSchema]