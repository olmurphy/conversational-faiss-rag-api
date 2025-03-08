# pylint: disable=no-self-argument

from typing import List, Optional

from api.schemas.base_request_response_model import BaseResponse
from fastapi import HTTPException
from pydantic import BaseModel, field_validator


class Source(BaseModel):
    title: str
    url: Optional[str] = None
    relevance_score: float


class Metadata(BaseModel):
    model_version: str
    generated_at: str
    retrieval_confidence: float


class AskQuestionInputSchema(BaseModel):
    """
    Represents the input schema for chat completion.

    Attributes:
        chat_query (str): The current query in the chat.
        chat_history (List[str]): The history of the chat messages.
    """

    chat_query: str

    @field_validator("chat_query")
    def validate_chat_query_length(cls, chat_query):
        max_length = 2000
        if len(chat_query) > max_length:
            raise HTTPException(
                status_code=413,
                detail=f"chat_query length exceeds {max_length} characters",
            )
        return chat_query


class AskQuestionSchema(BaseModel):
    """
    Represents the output schema for chat completion.

    Attributes:
        text (str): The completed message based on the input chat query and history.
        input_documents (List[Document]): List of input documents provided for the completion.
    """

    answer: str
    sources: List[Source]
    metadata: Metadata


AskQuestionOutputSchema = BaseResponse[AskQuestionSchema]
