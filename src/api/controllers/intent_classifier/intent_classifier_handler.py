import json 
import re
import os

from api.controllers.helper import format_response
from api.controllers.intent_classifier.model import APPLICATIONS, ENTITIES, EXAMPLES
from context import AppContext
from api.schemas.intent_classifier_schemas import IdentifyIntentInputSchema, IdentifyIntentOutputSchema
from api.schemas.base_request_response_model import ErrorResponse

from openai import OpenAI
from fastapi import HTTPException, Request, APIRouter, status



router = APIRouter()

API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv("OPENAI_BASE_URL")

client = OpenAI(
    api_key=API_KEY,  
    base_url=API_BASE_URL  
)


@router.post(
    "/identify-intent/",
    response_model=IdentifyIntentOutputSchema,
    responses={
        200: {"model": IdentifyIntentOutputSchema, "description": "Successful operation"},
        400: {"model": ErrorResponse, "description": "Bad Request"}
    },
    status_code=status.HTTP_200_OK,
    tags=["intent-classifier"]
)
async def identify_intent_endpoint(request: Request, query: IdentifyIntentInputSchema):
    """
    This is to identity the users intent using one of OpenAI LLM model
    """
    request_context: AppContext = request.state.app_context

    user_query = query.query

    if not user_query:
        request_context.logger.error({ "message": "Missing 'query' in request body", "data": user_query, "request_payload_size": user_query, "event": "REQUEST_RECEIVED"})
        return format_response(400, "Bad Request: Missing 'query' in request body", error= { "code": "BAD_REQUEST", "message": "query parameter is required" })
    
    request_context.logger.info({ "message": "intent classificiation", "data": user_query, "request_payload_size": user_query, "event": "REQUEST_RECEIVED"})

    # Call the OpenAI API
    result = identify_intent(user_query, request_context)
    request_context.logger.info({ "message": "openAI API response", "data": result, "request_payload_size": user_query, "event": "RESPONSE_RECEIVED"})

    return format_response(200, "Success", data=result)

def identify_intent(user_query: str, request_context: AppContext):
    """
    Sends a structured query to OpenAI for intent identification.
    """
    prompt = generate_intent_prompt(user_query)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Correct model name
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        response_text = response.choices[0].message.content.strip()
        response_text = re.sub(r"^```(json)?|```$", "", response_text, flags=re.MULTILINE).strip()
    
        # Parse the string response into a dictionary
        try:
            response_json = json.loads(response_text)  # Convert string to JSON
        except json.JSONDecodeError as e:
            request_context.logger.error({ "message": "Error Calling LLM", "data": None, "request_payload_size": user_query, "event": "BAD_REQUEST", "error": e })
            raise HTTPException(status_code=400, detail="Invalid JSON format from OpenAI response")

        return response_json  # Return as JSON instead of string
    except Exception as e:
        request_context.logger.error({ "message": "Error Calling LLM", "data": None, "request_payload_size": user_query, "event": "BAD_REQUEST", "error": e })
        raise HTTPException(status_code=500, detail=str(e))
    

# Define prompt generation function
def generate_intent_prompt(query: str) -> str:
    """
    Generates a structured prompt for intent identification.
    """
    prompt = f"""
    You are an intent identification agent. Your task is to:
    1. Determine the **application** the user should be redirected to based on their intent.
    2. Extract **entities** from the query.
    3. Generate **follow-up questions** if required entities are missing.
    4. Output the result in the specified JSON format.

    <DEFINITION>
    Applications:
    {APPLICATIONS}

    Entities:
    {ENTITIES}
    </DEFINITION>

    <EXAMPLES>
    {EXAMPLES}
    </EXAMPLES>

    <INPUT>
    {{"Query": "{query}"}}
    </INPUT>
    """
    return prompt.strip()
