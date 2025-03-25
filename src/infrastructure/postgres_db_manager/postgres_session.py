import contextlib
import time
import uuid
from typing import Dict, List, Union

from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import asc, event, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from api.schemas.user_interactions_schema import UpdateInteractionInputSchema
from configurations.postgres_config import PostgresDBConfig
from models.llm_invocation import LLMInvocations
from models.user_interactions import UserInteraction
from models.rag_retrievals import RagRetrievals


class PostgresSession:
    def __init__(self, postgres_db_config: PostgresDBConfig):
        self.logger = postgres_db_config.logger
        self.engine = None
        self.session_local = None

    async def initialize(self, postgres_db_config: PostgresDBConfig):
        self.engine = await self._create_postgres_engine(postgres_db_config)
        self.session_local = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine, class_=AsyncSession
        )
        self.logger.info({"message": "PostgreSQL connection established."})
        event.listen(
            self.engine.sync_engine,
            "before_cursor_execute",
            self._before_cursor_execute,
        )
        event.listen(
            self.engine.sync_engine, "after_cursor_execute", self._after_cursor_execute
        )

    async def _create_postgres_engine(self, postgres_db_config):
        engine_options = postgres_db_config.get_connection_pool_options()
        try:
            engine = create_async_engine(
                postgres_db_config.get_sqlalchemy_url(),
                **engine_options,
            )
            async with engine.connect() as conn:
                await conn.scalar(text("SELECT 1"))
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

    @contextlib.asynccontextmanager
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
        except Exception:
            await db.rollback()
            raise
        finally:
            await db.close()

    async def close(self):
        """Closes the engine and its connection pool."""
        self.engine.dispose()
        self.logger.info({"message": "PostgreSQL connection pool closed."})

    async def store_chat_message(
        self, session_id: uuid.UUID, messages: List[Union[AIMessage, HumanMessage]], interaction_time: float
    ):
        interaction_id = uuid.uuid4()
        start_time = time.time()
        try:
            # Data validation
            if not isinstance(session_id, uuid.UUID):
                raise ValueError("Invalid session_id")

            async with self.get_db() as db:
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
                    interaction_time=interaction_time,
                )
                self.logger.debug(
                    {
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
                        "message": f"Stored chat message for session_id: {session_id}",
                        "interaction_id": interaction_id,
                        "user_query": user_query,
                        "llm_response": llm_response,
                        "db_query_time": latency,
                    }
                )
                # store_message_latency.observe(latency)
                return interaction_id
        except (SQLAlchemyError, ValueError, TypeError) as e:
            self.logger.error(
                {
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

        start_time = time.time()
        self.logger.info(
            {
                "message": "Starting get_chat_history",
                "session_id": session_id,
                "limit": limit,
                "offset": offset,
            }
        )
        try:
            async with self.get_db() as db:
                query = (
                    select(UserInteraction)
                    .filter_by(session_id=session_id)
                    .order_by(asc(UserInteraction.created_at))
                    .limit(limit)
                    .offset(offset)
                )
                results = await db.execute(query)  # Await the execute coroutine
                rows = results.scalars().all()  # Now access scalars and all
                history: List[Dict] = []
                for row in rows:
                    if row.user_query:
                        history.append(HumanMessage(content=row.user_query))
                    if row.llm_response:
                        history.append(AIMessage(content=row.llm_response))

                latency = time.time() - start_time
                self.logger.info(
                    {
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
                    "message": f"Failed to retrieve chat history for session_id: {session_id}",
                    "error": str(e),
                }
            )
            raise
        except Exception as e:  # catch all other exceptions.
            self.logger.exception(
                {
                    "message": f"Unexpected error retrieving chat history for session_id: {session_id}",
                    "error": str(e),
                }
            )
            raise

    async def record_llm_invocation_metrics(
        self,
        llm_top_p,
        temperature,
        llm_latency,
        interaction_id: uuid.UUID,
        response,
    ):
        """Records metrics for LLM invocations."""
        response_metadata = response.response_metadata
        try:
            async with self.get_db() as db:
                llm_invocations = LLMInvocations(
                    interaction_id=interaction_id,
                    model_name=response_metadata.get("model_name"),
                    llm_latency=llm_latency,
                    llm_api_errors=0,
                    llm_temperature=temperature,
                    llm_top_p=llm_top_p,
                    system_fingerprint=response_metadata.get("system_fingerprint"),
                    finish_reason=response_metadata.get("finish_reason"),
                    completion_tokens=response_metadata.get("token_usage").get(
                        "completion_tokens"
                    ),
                    prompt_tokens=response_metadata.get("token_usage").get(
                        "prompt_tokens"
                    ),
                    input_tokens=response.usage_metadata["input_tokens"],
                    output_tokens=response.usage_metadata["output_tokens"],
                )
                db.add(llm_invocations)
                await db.commit()
                await db.refresh(
                    llm_invocations
                )  # refresh to get the current state of the database object.
                self.logger.info(
                    {
                        "message": "LLM invocation metrics recorded",
                        "llm_model": response_metadata.get("model_name"),
                        "latency": llm_latency,
                    }
                )
        except SQLAlchemyError as e:
            self.logger.error(
                {
                    "message": "Failed to record LLM invocation metrics",
                    "error": str(e),
                }
            )
            raise

    async def record_user_feedback(
        self, interaction_id: uuid.UUID, update_data: UpdateInteractionInputSchema
    ):
        self.logger.info(
            {"message": f"Recording user feedback for interaction ID: {interaction_id}"}
        )
        start_time = time.time()
        try:
            async with self.get_db() as db:
                user_interaction = await db.get(UserInteraction, interaction_id)

                if user_interaction is None:
                    self.logger.warning(
                        {"message": f"Interaction not found: {interaction_id}"}
                    )
                    raise ValueError(f"Interaction not found: {interaction_id}")

                for key, value in update_data.model_dump(exclude_unset=True).items():
                    setattr(user_interaction, key, value)
                db.add(user_interaction)
                await db.commit()
                await db.refresh(user_interaction)
        except ValueError as ve:
            self.logger.error(
                {"message": "Validation error recording feedback", "error": str(ve)}
            )
            # current_span = trace.get_current_span()
            # current_span.set_status(Status(StatusCode.INVALID_ARGUMENT))
            raise
        except SQLAlchemyError as sqle:
            self.logger.error(
                {"message": "Database error recording feedback", "error": str(sqle)},
            )
            # current_span = trace.get_current_span()
            # current_span.set_status(Status(StatusCode.ERROR))
            # Consider adding retry logic here for transient errors
            raise
        except Exception as e:
            self.logger.exception(
                {"message": "Unexpected error recording feedback", "error": str(e)}
            )
            # current_span = trace.get_current_span()
            # current_span.set_status(Status(StatusCode.ERROR))
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
       


    
    async def record_rag_retrieval_metrics(
        self,
        rag_invocation_time,
        retrieved_document_ids,
        retrieved_docs_count,
        similarity_scores,
        retrieval_latency,
        document_sources,
        document_lengths,
        interaction_id: uuid.UUID,
        ):
            """Records metrics for RAG retrieval."""
            retrieval_id = uuid.uuid4()
            try:
                async with self.get_db() as db:
                    db_start_time = time.time() #start db operations time.
                    rag_retrieval = RagRetrievals(
                        retrieval_id = retrieval_id,
                        rag_invocation_time=rag_invocation_time,
                        retrieved_document_ids=retrieved_document_ids,
                        retrieved_document_count=retrieved_docs_count, 
                        similarity_scores=similarity_scores, 
                        retrieval_latency=retrieval_latency,
                        document_sources=document_sources, 
                        document_lengths=document_lengths, 
                        interaction_id=interaction_id,
                    )
                    db.add(rag_retrieval) 
                    await db.commit() 
                    await db.refresh(rag_retrieval)   
                    db_end_time = time.time() #end db operations time
                    self.logger.info(
                        {
                            "message": "RAG retrieval metrics recorded",
                            "data": {
                                "retrieval_id": str(retrieval_id),
                                "interaction_id": str(interaction_id),
                                "rag_invocation_time": rag_invocation_time,
                                # "faiss_retrieval_time": faiss_retrieval_time,
                                "retrieved_docs_count": retrieved_docs_count,
                                "retrieval_latency": retrieval_latency,
                                "document_sources_count": len(document_sources),
                                "document_lengths_count": len(document_lengths),
                                "similarity_scores_count": len(similarity_scores),
                                "retrieved_document_ids_count": len(retrieved_document_ids),
                                "db_execution_time": db_end_time - db_start_time,
                            }
                        },
                        extra={"metric_type": "rag_retrieval_metrics"},  # Add a custom dimension
                    )
            except SQLAlchemyError as e:
                self.logger.error(
                    {
                        "message": "Failed to record Rag retrieval metrics",
                        "retrieval_id": str(retrieval_id),
                        "interaction_id": str(interaction_id),
                        "error": str(e),
                    },
                    exc_info=True, #include traceback
                    extra={"metric_type": "rag_retrieval_metrics_error"}, #add custom dimension
                )
                raise
           

