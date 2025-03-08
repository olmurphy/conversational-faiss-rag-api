import logging
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from configurations.postgres_config import PostgresDBConfig

Base = declarative_base()


class PostgresSession:
    def __init__(self, postgres_db_config: PostgresDBConfig):
        self.logger = postgres_db_config.logger
        self.engine = self._create_postgres_engine(postgres_db_config)
        self.session_local = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.logger.info({"message": "PostgreSQL connection established."})

    def _create_postgres_engine(self, postgres_db_config):
        engine_options = postgres_db_config.get_connection_pool_options()
        try:
            engine = create_engine(
                postgres_db_config.get_sqlalchemy_url(),
                **engine_options,
            )
            engine.connect().close() #test connection.
            return engine
        except SQLAlchemyError as e:
            self.logger.error({"message": "Error creating or testing engine", "error": e, "data": f"{postgres_db_config}"})
            raise

    def get_db(self):
        db = self.session_local()
        try:
            yield db
        finally:
            db.close()

    def close(self):
        """Closes the engine and its connection pool."""
        self.engine.dispose()
        self.logger.info({"message": "PostgreSQL connection pool closed."})
