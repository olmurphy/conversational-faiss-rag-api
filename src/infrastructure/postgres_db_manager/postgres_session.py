import logging
import uuid
from typing import List

from configurations.postgres_config import PostgresDBConfig
from models.user_interactions import UserInteraction
from sqlalchemy import create_engine, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

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
            engine.connect().close()  # test connection.
            return engine
        except SQLAlchemyError as e:
            self.logger.error(
                {
                    "message": "Error creating or testing engine",
                    "error": e,
                    "data": f"{postgres_db_config}",
                }
            )
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

    def store_chat_message(self, session_id, messages):
        interaction_id = uuid.uuid4()
        try:
            with self.get_db() as db:
                user_interaction = UserInteraction(
                    interaction_id=interaction_id,
                    session_id=session_id,
                    user_query=(
                        messages[-2].get("user_query") if len(messages) >= 2 else None
                    ),
                    llm_response=messages[-1].get("llm_response") if messages else None,
                    chat_history=messages,
                )
                db.add(user_interaction)
                db.commit()
                self.logger.debug(
                    {
                        "message": f"Stored chat message for session_id: {session_id}",
                        "interaction_id": interaction_id,
                        "data": messages,
                    }
                )
        except SQLAlchemyError as e:
            self.logger.error(
                {
                    "message": f"Failed to store chat message for session_id: {session_id}",
                    "data": messages,
                    "error": e,
                }
            )
            raise

    def get_chat_history(self, session_id: uuid.UUID) -> List[dict]:
        """Retrieves the chat history for a given session."""
        try:
            with self.get_db() as db:
                query = (
                    select(UserInteraction)
                    .filter_by(session_id=session_id)
                    .order_by(UserInteraction.created_at)
                )
                results = db.execute(query).scalars().all()
                history = []
                for row in results:
                    history.append(
                        {
                            "user_query": row.user_query,
                            "llm_response": row.llm_response,
                            "created_at": row.created_at,
                            "interaction_id": row.interaction_id,
                            "session_id": row.session_id,
                            "edited_response": row.edited_response,
                            "positive_feedback": row.positive_feedback,
                            "negative_feedback": row.negative_feedback,
                            "feedback_reason": row.feedback_reason,
                            "rating": row.rating,
                            "interaction_time": row.interaction_time,
                            "clicks": row.clicks,
                            "scroll_depth": row.scroll_depth,
                            "number_of_turns": row.number_of_turns,
                        }
                    )
                return history
        except SQLAlchemyError as e:
            self.logger.error(
                {
                    "message": f"Failed to retrieve chat history for session_id: {session_id}",
                    "error": e,
                }
            )
            raise
