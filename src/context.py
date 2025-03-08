from logging import Logger
from typing import Optional

from attrs import define

# from infrastracture.metrics.manager import MetricsManager
from configurations.service_model import ConfigSchema
from configurations.variables_model import Variables
from starlette.requests import Request
from infrastracture.redis_manager.redis_session import RedisSession
from infrastracture.redis_manager.redis_auth import RedisAuth


class RequestContext:
    def __init__(self, logger: Logger, env_vars: Variables, request: Request):
        self._logger = logger
        if request:
            self._headers_to_proxy = self._build_proxy_headers(env_vars, request)

    def _build_proxy_headers(self, env_vars: Variables, request: Request):
        # Extract headers from the request where the header name is in the HEADERS_TO_PROXY list in the environment variables
        if not env_vars.HEADERS_TO_PROXY:
            return {}
        headers_to_proxy = env_vars.HEADERS_TO_PROXY.split(",")
        headers = {}
        for header in headers_to_proxy:
            if header in request.headers:
                headers[header] = request.headers[header]

        return headers

    @property
    def logger(self):
        return self._logger

    @property
    def headers_to_proxy(self):
        return self._headers_to_proxy


@define
class AppContextParams:
    logger: Logger
    # metrics_manager: MetricsManager
    env_vars: Variables
    configurations: ConfigSchema
    request_context: Optional[RequestContext] = None
    redis_session: Optional[RedisSession] = None # Add this line
    redis_auth: Optional[RedisAuth] = None

class AppContext:
    """
    The AppContext class serves as a container for key components used across the application.

    It holds instances of the logger, metrics manager, environment variables, and configurations,  allowing these
    instances to be shared and easily accessed throughout the application.
    """

    def __init__(self, params: AppContextParams):
        self._logger = params.logger
        # self._metrics_manager = params.metrics_manager
        self._env_vars = params.env_vars
        self._configurations = params.configurations
        self._request_context = (
            params.request_context if params.request_context else None
        )
        self._redis_session = params.redis_session # Add this line
        self._redis_auth = params.redis_auth


    @property
    def logger(self):
        return self._logger

    # @property
    # def metrics_manager(self):
    #     return self._metrics_manager

    @property
    def lru_cahce(self):
        return self._lru_cache

    @property
    def env_vars(self):
        return self._env_vars

    @property
    def configurations(self):
        return self._configurations

    @property
    def request_context(self):
        return self._request_context

    @property
    def redis_session(self):
        return self._redis_session

    @property
    def redis_auth(self):
        return self._redis_auth

    def create_request_context(self, request_logger, request: Request = None):
        """
        Creates a new AppContext with a different logger instance, while keeping references to the original context creating a new request context.
        """
        params = AppContextParams(
            logger=request_logger,
            # metrics_manager=self._metrics_manager,
            env_vars=self._env_vars,
            configurations=self._configurations,
            request_context=RequestContext(
                logger=request_logger,
                env_vars=self._env_vars,
                request=request if request else None,
            ),
            redis_session = self._redis_session,
            redis_auth=self._redis_auth
        )
        return AppContext(params)
