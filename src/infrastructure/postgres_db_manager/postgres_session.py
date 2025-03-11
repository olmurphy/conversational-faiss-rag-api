import time
import uuid
from contextlib import contextmanager  # add this import.
from typing import Dict, List, Union

from configurations.postgres_config import PostgresDBConfig
from langchain_core.messages import AIMessage, HumanMessage
from models.user_interactions import UserInteraction
from sqlalchemy import asc, event, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


class PostgresSession:
    def __init__(self, postgres_db_config: PostgresDBConfig):
        self.logger = postgres_db_config.logger
        self.engine = self._create_postgres_engine(postgres_db_config)
        self.session_local = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine, class_=AsyncSession
        )
        self.logger.info({"message": "PostgreSQL connection established."})
        event.listen(self.engine.sync_engine, "before_cursor_execute", self._before_cursor_execute) #attach to sync_engine.
        event.listen(self.engine.sync_engine, "after_cursor_execute", self._after_cursor_execute) #attach to sync_engine.

    def _create_postgres_engine(self, postgres_db_config):
        engine_options = postgres_db_config.get_connection_pool_options()
        try:
            engine = create_async_engine(
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

    @contextmanager
    async def get_db(self):
        """
        Provides a SQLAlchemy database session as a context manager.

        This method uses the `@contextmanager` decorator to transform a generator
        function into a context manager. This allows the database session to be
        used within a `with` statement, ensuring that the session is properly
        closed after it is no longer needed.

        Why use context managers?

        - **Automatic Resource Management:** Context managers handle the setup and
          cleanup of resources, in this case, a database session. This ensures
          that the session is closed, even if exceptions occur within the `with` block.

        - **Improved Readability:** The `with` statement makes the code cleaner and
          more readable, clearly indicating the scope within which the database
          session is valid.

        - **Prevention of Resource Leaks:** By automatically closing the session,
          context managers prevent resource leaks, which can occur if sessions are
          not explicitly closed.

        How it works:

        1.  A new database session (`db`) is created using `self.session_local()`.
        2.  The `yield db` statement yields the session, making it available
            to the code within the `with` block.
        3.  After the `with` block finishes (either normally or due to an
            exception), the code in the `finally` block is executed, which
            closes the database session (`db.close()`).

        Yields:
            Session: A SQLAlchemy database session object.
        """
        db = self.session_local()
        try:
            yield db
        finally:
            db.close()

    async def close(self):
        """Closes the engine and its connection pool."""
        self.engine.dispose()
        self.logger.info({"message": "PostgreSQL connection pool closed."})

    async def store_chat_message(
        self, session_id: uuid.UUID, messages: List[Union[AIMessage, HumanMessage]]
    ):
        request_id = uuid.uuid4()
        interaction_id = uuid.uuid4()
        start_time = time.time()
        try:
            # Data validation
            if not isinstance(session_id, uuid.UUID):
                raise ValueError("Invalid session_id")

            with await self.get_db() as db:
                user_query = None
                llm_response = None
                if len(messages) >= 2 and isinstance(messages[-2], HumanMessage):
                    user_query = messages[-2].content
                if messages and isinstance(messages[-1], AIMessage):
                    llm_response = messages[-1].content

                user_interaction = UserInteraction(
                    interaction_id=interaction_id,
                    session_id=session_id,
                    user_query=user_query,
                    llm_response=llm_response,
                )
                self.logger.debug(
                    {
                        "request_id": request_id,
                        "message": f"Stored chat message for session_id: {session_id}",
                        "interaction_id": interaction_id,
                        "user_query": user_query,
                        "llm_response": llm_response,
                    }
                )
                db.add(user_interaction)
                await db.commit()
                await db.refresh(user_interaction)  # use await and refresh

                latency = time.time() - start_time
                self.logger.debug(
                    {
                        "request_id": request_id,
                        "message": f"Stored chat message for session_id: {session_id}",
                        "interaction_id": interaction_id,
                        "user_query": user_query,
                        "llm_response": llm_response,
                        "db_query_time": latency
                    }
                )
                # store_message_latency.observe(latency)
                return interaction_id
        except (SQLAlchemyError, ValueError, TypeError) as e:
            self.logger.error(
                {
                    "request_id": request_id,
                    "message": f"Failed to store chat message for session_id: {session_id}",
                    "session_id": session_id,
                    "messages": messages,
                    "error": str(e),
                }
            )
            raise

    async def get_chat_history(
        self, session_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> List[Union[AIMessage, HumanMessage]]:
        """Retrieves the chat history for a given session."""

        request_id = uuid.uuid4()  # Generate a request ID for tracing
        start_time = time.time()
        self.logger.info(
            {
                "request_id": request_id,
                "message": "Starting get_chat_history",
                "session_id": session_id,
                "limit": limit,
                "offset": offset,
            }
        )
        try:
            with await self.get_db() as db:
                # Server-side cursor for better performance with large datasets
                query = (
                    select(UserInteraction)
                    .filter_by(session_id=session_id)
                    .order_by(asc(UserInteraction.created_at))
                    .limit(limit)
                    .offset(offset)
                ).execution_options(stream_results=True)
                results = db.execute(query).scalars().all()
                history: List[Dict] = []
                for row in results:
                    if row.user_query:
                        history.append(HumanMessage(content=row.user_query))
                    if row.llm_response:
                        history.append(AIMessage(content=row.llm_response))

                latency = time.time() - start_time
                self.logger.info(
                    {
                        "request_id": request_id,
                        "message": "Successfully retrieved chat history",
                        "session_id": session_id,
                        "history_length": len(history),
                        "db_query_time": latency,
                    }
                )
                # get_history_latency.observe(latency)
                return history
        except SQLAlchemyError as e:
            self.logger.error(
                {
                    "request_id": request_id,
                    "message": f"Failed to retrieve chat history for session_id: {session_id}",
                    "error": str(e),
                }
            )
            raise
        except Exception as e:  # catch all other exceptions.
            self.logger.exception(
                {
                    "request_id": request_id,
                    "message": f"Unexpected error retrieving chat history for session_id: {session_id}",
                    "error": str(e),
                }
            )
            raise

    def _before_cursor_execute(
        self, conn, cursor, statement, parameters, context, executemany
    ):
        conn.info.setdefault("query_start_time", []).append(time.time())

    def _after_cursor_execute(
        self, conn, cursor, statement, parameters, context, executemany
    ):
        start_time = conn.info.get("query_start_time", []).pop(0)
        end_time = time.time()
        # query_execution_time.observe(end_time - start_time) # need prometheus client.
        # query_types.labels(query_type=statement.split(" ")[0].upper()).inc()
        # queries_per_second.inc()
