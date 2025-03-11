import json
import uuid
from logging import Logger
from typing import Dict, List, Union

from infrastructure.postgres_db_manager.postgres_session import PostgresSession
from infrastructure.redis_manager.redis_session import RedisSession
from langchain_core.messages import AIMessage, HumanMessage


class UserSession:
    CACHE_TTL = 60 * 60  # one hour

    def __init__(
        self,
        redis_session: RedisSession,
        postgres_session: PostgresSession,
        logger: Logger = None,
    ):
        self.redis_session = redis_session
        self.postgres_session = postgres_session
        self.logger = logger

    async def get_chat_history(self, session_id: uuid.UUID):
        """
        Cache-Aside Pattern:
        1. Try Redis first
        2. If cache miss → load from Postgres
        3. Update Redis (avoid thundering herd problem)
        """
        request_id = uuid.uuid4()
        try:
            cached_data = await self.redis_session.get_chat_history(session_id=session_id)

            if cached_data:
                self.logger.debug(
                    {
                        "request_id": request_id,
                        "message": "Cache hit for chat history",
                        "session_id": session_id,
                    }
                )
                return cached_data
            self.logger.debug(
                {
                    "request_id": request_id,
                    "message": "Cache miss - loading chat history from DB",
                    "session_id": session_id,
                }
            )
            chat_history = await self.postgres_session.get_chat_history(session_id=session_id)

            if chat_history:
                self.redis_session.store_chat_message(session_id, chat_history)
                self.logger.debug(
                    {
                        "request_id": request_id,
                        "message": "Chat history loaded from DB and stored in cache",
                        "session_id": session_id,
                    }
                )

                return chat_history
            self.logger.warning(
                {
                    "request_id": request_id,
                    "message": "Chat history not found in DB.",
                    "session_id": session_id,
                }
            )
            return []  # return empty list when no history is found.
        except Exception as e:
            if self.logger:
                self.logger.error(
                    {
                        "request_id": request_id,
                        "message": f"Error retrieving chat history for session_id: {session_id}",
                        "error": str(e),
                    }
                )
            return []  # Return empty list on error

    def store_chat_message(self, session_id: uuid.UUID, messages: List[Union[AIMessage, HumanMessage]]):
        """
        Save the last user query and LLM response to Postgres.
        Invalidate Redis cache.
        """
        request_id = uuid.uuid4()

        try:    
            interaction_id = self.postgres_session.store_chat_message(session_id, messages)
            self.redis_session.delete_chat_history(session_id)
           
            self.logger.debug(
                {
                    "request_id": request_id,
                    "message": "Chat message stored and cache invalidated",
                    "session_id": session_id,
                }
            )
            return interaction_id
        except Exception as e:
            
            self.logger.error(
                {
                    "request_id": request_id,
                    "message": f"Error storing chat message for session_id: {session_id}",
                    "error": str(e),
                }
            )
            raise
