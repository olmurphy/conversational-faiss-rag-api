from typing import List

EXCLUDED_PATHS: List[str] = [
    "/readiness",
    "/liveness",
    "/openapi.json",
    "/docs",
    "/favicon.ico",
    "/metrics"
]

REQUEST_ID_HEADER = "x-request-id"
TRANSACTION_ID_HEADER = "x-transaction-id"
SESSION_ID_HEADER = "x-session-id"
CACHE_SESSION_ID_HEADER = "x-cache-session-id"
PERSON_NUMBER_HEADER = "x-person-number"
PROCESSING_TIME_HEADER = "x-processing-time"
ROUTE_HEADER = "x-route"

ORIGINS: List[str] = [
    "*"
]