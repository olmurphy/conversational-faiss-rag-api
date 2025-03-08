from typing import Generic, TypeVar, Optional, Dict, Any
from pydantic import BaseModel, Field

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    status: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Descriptive message")
    data: Optional[T] = Field(None, description="The response data, if successful.")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details, if any.")

class ErrorResponse(BaseModel):
    status: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Error message")
    error: Dict[str, Any] = Field(..., description="Error details")