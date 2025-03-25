import time

from configurations.middleware_config import EXCLUDED_PATHS
from context import AppContext
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = str(response.status_code)
            error_type = ""  # No error occurred
        except ValueError as e:
            status_code = "400"
            error_type = type(e).__name__
            raise e
        except FileNotFoundError as e:
            status_code = "404"
            error_type = type(e).__name__
            raise e
        except Exception as e:
            status_code = "500"
            error_type = type(e).__name__
            raise e
        finally:
            duration = time.time() - start_time
            path = request.url.path
            method = request.method
            app_context: AppContext = request.state.app_context
            app_context.metrics_manager.requests_total.labels(
                method=method, endpoint=path, status=status_code, error_type=error_type
            ).inc()
            app_context.metrics_manager.request_latency.labels(
                method=method, endpoint=path
            ).observe(duration)

        return response
