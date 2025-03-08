import datetime
import json
import uuid
from logging import Logger

from infrastructure.postgres_db_manager.postgres_session import PostgresSession
from infrastructure.redis_manager.redis_session import (
    CHAT_HISTORY_KEY_SUFFIX,
    SESSION_KEY_PREFIX,
    RedisSession,
)


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

    def get_chat_history(self, session_id):
        """
        Cache-Aside Pattern:
        1. Try Redis first
        2. If cache miss → load from Postgres
        3. Update Redis (avoid thundering herd problem)
        """
        cache_key = f"{SESSION_KEY_PREFIX}{session_id}{CHAT_HISTORY_KEY_SUFFIX}"
        cached_data = self.redis_session.get_chat_history(session_id=session_id)

        if cached_data:
            print("Cache hit")
            return json.loads(cached_data)

        print("Cache miss - loading from DB")
        chat_history = self._load_chat_history_from_db(session_id)
        if chat_history:
            self.redis_session.store_chat_message(session_id, chat_history)
        return chat_history

    def store_chat_message(self, session_id, messages):
        """
        Save the last 2 messages to the cache and persist everything in Postgres.
        Invalidate cache after storing.
        """
        # 1. Persist to database
        interaction_id = str(uuid.uuid4())
        with self.get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO user_interactions (
                        interaction_id, session_id, user_query, 
                        llm_response, chat_history, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                    (
                        interaction_id,
                        session_id,
                        messages[-2]["user_query"],
                        messages[-1]["llm_response"],
                        json.dumps(messages),
                        datetime.utcnow(),
                    ),
                )
                conn.commit()

        # 2. Invalidate Redis cache (force fresh fetch)
        cache_key = f"chat_history:{session_id}"
        self.redis_session.delete(cache_key)

    def _load_chat_history_from_db(self, session_id):
        """Load chat history from the database"""
        with self.get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT chat_history 
                    FROM user_interactions
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    (session_id,),
                )
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
        return []
