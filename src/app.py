import os
from contextlib import asynccontextmanager

import uvicorn
from api.controllers.core.liveness import liveness_handler
from api.controllers.core.metrics import metrics_handler
from api.controllers.core.readiness import readiness_handler
from api.controllers.rag_handler import rag_handler
from api.controllers.user_interactions_handler import user_interactions_handler
from api.middlewares.app_context_middleware import AppContextMiddleware
from api.middlewares.authentication_middleware import AuthenticationMiddleware
from api.middlewares.error_handling_middleware import ErrorHandlingMiddleware
from api.middlewares.logger_middleware import LoggerMiddleware
from api.middlewares.metrics_middleware import MetricsMiddleware
from configurations.configuration import get_configuration
from configurations.postgres_config import PostgresDBConfig
from configurations.redis_config import RedisConfig
from configurations.variables import get_variables
from context import AppContext, AppContextParams
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from infrastructure.logger import get_logger
from infrastructure.metrics_manager.metrics_manager import MetricsManager
from infrastructure.postgres_db_manager.postgres_session import PostgresSession
from infrastructure.redis_manager.redis_auth import RedisAuth
from infrastructure.redis_manager.redis_session import RedisSession
from configurations.middleware_config import ORIGINS

load_dotenv()


def create_app(context: AppContext, lifespan) -> FastAPI:
    app = FastAPI(
        redoc_url=None,
        title=context.env_vars.SERVICE_NAME,
        version="0.0.1",
        lifespan=lifespan,
    )
    app.add_middleware(AppContextMiddleware, app_context=context)
    app.add_middleware(ErrorHandlingMiddleware, logger=context.logger)
    app.add_middleware(LoggerMiddleware, logger=context.logger)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(AuthenticationMiddleware, app_context=context)
    app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)
    app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=["*"], allow_headers=["*"], allow_credentials=True)

    app.include_router(liveness_handler.router)
    app.include_router(readiness_handler.router)
    app.include_router(rag_handler.router)
    app.include_router(user_interactions_handler.router)
    app.include_router(metrics_handler.router)

    return app


if __name__ == "__main__":
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    logger = get_logger()
    env_vars = get_variables(logger)
    metrics_manager = MetricsManager(namespace=env_vars.SERVICE_NAME)
    logger.debug({"message": "env var", "data": f"var is: {env_vars}"})
    configurations = get_configuration(env_vars.CONFIGURATION_PATH, logger)
    logger.debug(
        {"message": "configuration values", "data": f"config is: {configurations}"}
    )

    postgres_db_config = PostgresDBConfig(
        db=env_vars.PG_DB,
        host=env_vars.PG_HOST,
        password=env_vars.PG_PASSWORD,
        port=env_vars.PG_PORT,
        user=env_vars.PG_USER,
        ssl_ca_cert_path=env_vars.PG_CERT_BASE64,
        postgres_pool_config=configurations.postgresDB,
        logger=logger,
    )
    postgres_session = PostgresSession(postgres_db_config=postgres_db_config)

    redis_config = RedisConfig(
        redis_url=env_vars.REDIS_URL,
        redis_cert_path=env_vars.REDIS_CERT_PATH,
        logger=logger,
        max_connections=configurations.redis.max_connections,
    )  # Initialize RedisConfig
    redis_session = RedisSession(
        redis_config, expiration=configurations.redis.time_to_live
    )  # Initialize RedisSession
    redis_auth = RedisAuth(redis_config=redis_config)

    app_context = AppContext(
        params=AppContextParams(
            logger=logger,
            metrics_manager=metrics_manager,
            env_vars=env_vars,
            configurations=configurations,
            redis_session=redis_session,
            redis_auth=redis_auth,
            postgres_session=postgres_session,
        )
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await app_context.postgres_session.initialize(postgres_db_config)
        logger.info("PostgresSession initialized.")
        yield

    application = create_app(app_context, lifespan=lifespan)

    logger.info(
        {
            "message": f"OpenAPI specs can be found at http://localhost:{app_context.env_vars.PORT}/docs"
        }
    )

    uvicorn.run(
        application,
        host="0.0.0.0",  # nosec B104 # binding to all interfaces is required to expose the service in containers
        port=app_context.env_vars.PORT,
        log_level="error",
    )
