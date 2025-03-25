from datetime import datetime, timezone

from api.controllers.helper import format_response
from api.controllers.rag_handler.helper import format_sources
from api.schemas.base_request_response_model import ErrorResponse
from api.schemas.rag_handler_schemas import (AskQuestionInputSchema,
                                             AskQuestionOutputSchema)
from application.assistance.service import AssistantService
from configurations.middleware_config import SESSION_ID_HEADER
from context import AppContext
from fastapi import APIRouter, Request, status

router = APIRouter()


@router.post(
    "/ask-question/",
    response_model=AskQuestionOutputSchema,
    responses={
        200: {"model": AskQuestionOutputSchema, "description": "Successful operation"},
        400: {"model": ErrorResponse, "description": "Bad Request"},
    },
    status_code=status.HTTP_200_OK,
    tags=["question-answering"],
)
async def ask_question_endpoint(request: Request, chat_query: AskQuestionInputSchema):
    """
    Processes a user query and returns an AI-generated response with relevant sources.

    This endpoint receives a user query, processes it using an AI model, and returns the generated response along with relevancy scores.
    """
    request_context: AppContext = request.state.app_context

    user_query = chat_query.chat_query
    session_id = request.headers.get(SESSION_ID_HEADER)

    if not user_query:
        request_context.logger.error(
            {"message": "Missing 'query' in request body", "event": "BAD_REQUEST"}
        )
        return format_response(
            status.HTTP_400_BAD_REQUEST,
            "Bad Request: Missing 'query' in request body",
            error={"code": "BAD_REQUEST", "message": "query parameter is required"},
        )
    assistant_service = AssistantService(app_context=request_context)
    response, retrieved_docs, interaction_id = await assistant_service.chat_completion(
        user_query, session_id
    )

    sources = format_sources(retrieved_docs)

    return format_response(
        status=status.HTTP_200_OK,
        message="Success",
        data={
            "answer": response.content,
            "sources": sources,
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model": response.response_metadata.get("model_name", "unknown"),
            },
            "interaction_id": str(interaction_id),
        },
    )
