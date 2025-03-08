from context import AppContext
from starlette.middleware.base import BaseHTTPMiddleware


class AppContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject a custom application context into the Starlette app state
    """

    def __init__(self, app, app_context: AppContext):
        super().__init__(app)
        self.app_context = app_context

    async def dispatch(self, request, call_next):
        excluded_paths = [
            "/readiness",
            "/liveness",
            "/openapi.json",
            "/docs"
        ]

        if request.url.path not in excluded_paths:
            request.state.app_context = self.app_context.create_request_context(
                request.state.logger,
                request=request,
            )

        response = await call_next(request)

        return response
