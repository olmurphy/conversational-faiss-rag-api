import logging
import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_ID_HEADER = "x-request-id"
TRANSACTION_ID_HEADER = "x-transaction-id"
SESSION_ID_HEADER = "x-session-id"
CACHE_SESSION_ID_HEADER = "x-cache-session-id"
PERSON_NUMBER_HEADER = "x-person-number"
PROCESSING_TIME_HEADER = "x-processing-time"
ROUTE_HEADER = "x-route"


class ReqIdLoggerAdapter(logging.LoggerAdapter):
    """
    Logger Adapter to add reqid to the log records.
    """

    def process(self, msg, kwargs):
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"]["request_id"] = self.extra.get("request_id", str(uuid.uuid4()))
        kwargs["extra"]["transaction_id"] = self.extra.get(
            "transaction_id", str(uuid.uuid4())
        )
        kwargs["extra"]["session_id"] = self.extra.get("session_id", str(uuid.uuid4()))
        kwargs["extra"]["cache_session-id"] = self.extra.get(
            "cache-session_id", str(uuid.uuid4())
        )
        kwargs["extra"]["person_number"] = self.extra.get(
            "person_number", str(uuid.uuid4())
        )
        return msg, kwargs


class LoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add the logger to the request and logs request info
    """

    def __init__(self, app, logger):
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request, call_next):
        excluded_paths = [
            "/readiness",
            "/liveness",
            "/openapi.json",
            "/docs"
        ]

        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
        transaction_id = request.headers.get(
            TRANSACTION_ID_HEADER, str(uuid.uuid4())
        )  # Default to UUID if missing
        session_id = request.headers.get(SESSION_ID_HEADER, None)
        cache_session_id = request.headers.get(CACHE_SESSION_ID_HEADER, "unkown")
        person_number = request.headers.get(PERSON_NUMBER_HEADER, "unkown")

        # Get User / client information using this API
        client_ip = request.headers.get("X-Forwarded-For", request.client.host)
        user_agent = request.headers.get("User-Agent", "Unknown")
        referer = request.headers.get("Referer", "None")
        content_type = request.headers.get("Content-Type", "Unknown")
        cookies = request.cookies
        if not session_id:
            new_header = MutableHeaders(request._headers)
            session_id = str(uuid.uuid4())
            new_header[SESSION_ID_HEADER] = session_id
            request._headers = new_header
            request.scope.update(headers=request.headers.raw)

        log_extra = {
            "request_id": request_id,
            "transaction_id": transaction_id,
            "session_id": session_id,
            "cache_session_id": cache_session_id,
            "person_number": person_number,
        }
        request_logger = ReqIdLoggerAdapter(self.logger, log_extra)

        if request.url.path not in excluded_paths:
            request_logger.debug(
                {
                    "message": f"{request.method} {request.url.path}",
                    "http": {
                        "method": request.method,
                        "path": request.url.path,
                    },
                    "user_metadata": {
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                        "referer": referer,
                        "content_type": content_type,
                        "cookies": cookies,
                    },
                }
            )
            start_time = time.time()

        request.state.logger = request_logger
        response = await call_next(request)

        if request.url.path not in excluded_paths:
            duration = time.time() - start_time
            response.headers[PROCESSING_TIME_HEADER] = str(duration)
            response.headers[REQUEST_ID_HEADER] = request_id
            response.headers[ROUTE_HEADER] = request.url.path
            response.headers[SESSION_ID_HEADER] = session_id

            request_logger.debug(
                {
                    "message": f"{request.method} {request.url.path}",
                    "http": {
                        "method": request.method,
                        "path": request.url.path,
                        "status": response.status_code,
                        "duration": duration,
                    },
                    "user_metadata": {
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                        "referer": referer,
                        "content_type": content_type,
                        "cookies": cookies,
                    },
                }
            )

        return response
