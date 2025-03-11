import asyncio
import logging
import traceback
import uuid

import tenacity
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling unhandled exceptions and providing a consistent error response.

    This middleware catches exceptions raised during request processing, logs them,
    and returns a JSON response with a 500 Internal Server Error status code.

    Attributes:
        app: The Starlette application instance.
        logger: A logging.Logger instance for logging errors.
        debug: A boolean flag indicating whether to include stack traces in the error response.
    """
    def __init__(self, app, logger: logging.Logger, debug: bool = False):
        super().__init__(app)
        self.logger = logger
        self.debug = debug

    async def dispatch(self, request: Request, call_next):
        """
        Dispatches the request through the middleware.

        This method wraps the request processing in a try-except block to catch unhandled exceptions.
        It also implements retry logic using tenacity.

        Args:
            request: The incoming Request object.
            call_next: The next middleware or route handler in the chain.

        Returns:
            A JSONResponse object containing the error details or the response from the next handler.
        """
        try:
            response = await self._retry_and_circuit_breaker(request, call_next)
            return response
        except Exception as exc:
            request_logger = getattr(request.state, "logger", self.logger) #gets the request specific logger, or the general logger.

            error_data = {
                "message": "Unhandled exception",
                "error": str(exc),
                "error_type": type(exc).__name__,
                "request_method": request.method,
                "request_path": request.url.path,
                "trace_id": uuid.uuid4(),
                "span_id": uuid.uuid4(),
                "headers": dict(request.headers),
            }
            print(exc)
            request_logger.exception({"message": "Unhandled exception", "error": error_data}) #logs the exception with a stack trace.
            
            error_response = {"detail": "Internal Server Error"}

            if self.debug:
                error_response["stack_trace"] = traceback.format_exc()
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response,
            )
    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),  # Retry 3 times
        wait=tenacity.wait_exponential(multiplier=1, max=10),  # Exponential backoff
        retry=tenacity.retry_if_exception_type(Exception), #retry any exception
        before_sleep=tenacity.before_sleep_log(logging.getLogger("tenacity"), logging.WARNING), #log retry attempts
        reraise=True #Reraise the last exception if all retries fail.
    )
    async def _retry_and_circuit_breaker(self, request, call_next):
        """
        Applies retry logic to the request processing.

        This method uses tenacity to retry the request processing in case of exceptions.

        Args:
            request: The incoming Request object.
            call_next: The next middleware or route handler in the chain.

        Returns:
            The response from the next handler after successful processing or after retries.
        """
        #Simulating a service call that might fail.
        return await call_next(request)
    
