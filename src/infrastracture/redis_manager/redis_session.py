import json
import time
from typing import Dict, Optional

import redis
from configurations.redis_config import RedisConfig
from infrastracture.redis_manager.util import (deserialize_message,
                                               serialize_message)

SESSION_KEY_PREFIX = "session:"
CHAT_HISTORY_KEY_SUFFIX = ":chat_history"


class RedisSession:
    def __init__(self, redis_config: RedisConfig, expiration=3600):
        self.redis_pool = redis_config.get_redis_client()
        self.logger = redis_config.logger
        self.expiration = expiration
        if not self.redis_pool:
            raise ValueError("Redis client initialization failed")
        self.logger.info({"message": "RedisSession initialized successfully."})

    def _get_redis_connection(self):
        return redis.Redis(connection_pool=self.redis_pool)

    def set_session(self, session_id, data):
        key = f"{SESSION_KEY_PREFIX}{session_id}"
        try:
            with self._get_redis_connection() as redis_conn:

                self.logger.debug(
                    {"message": f"Setting the session with {session_id}", "data": data}
                )
                redis_conn.set(key, json.dumps(data), self.expiration)
        except redis.exceptions.RedisError as e:
            self.logger.error(
                {"message": f"Failed to set session {session_id}: {e}", "error": e}
            )

    def get_session(self, session_id):
        key = f"{SESSION_KEY_PREFIX}{session_id}"
        try:
            with self._get_redis_connection() as redis_conn:

                self.logger.debug({"message": "Fetching the session from Redis"})
                session_data = redis_conn.get(key)
                if session_data:
                    self.logger.debug(
                        {
                            "message": "Fetch from Redis Successful",
                            "data": json.loads(session_data),
                        }
                    )
                    return json.loads(session_data)
                else:
                    return None
        except redis.exceptions.RedisError as e:
            self.logger.error(
                {"message": f"Failed to get session {session_id}", "error": e}
            )
            return None

    def delete_session(self, session_id):
        key = f"{SESSION_KEY_PREFIX}{session_id}"
        chat_history_key = f"{SESSION_KEY_PREFIX}{session_id}{CHAT_HISTORY_KEY_SUFFIX}"
        try:
            with self._get_redis_connection() as redis_conn:
                self.logger.debug({"message": f"Deleting {session_id}"})
                pipeline = redis_conn.pipeline()
                pipeline.delete(key)
                pipeline.delete(chat_history_key)
                pipeline.execute()  # execute the pipeline.
        except redis.exceptions.RedisError as e:
            self.logger.error(
                {"message": f"Failed to delete session {session_id}", "error": e}
            )

    def store_chat_message(self, session_id, messages):
        key = f"{SESSION_KEY_PREFIX}{session_id}{CHAT_HISTORY_KEY_SUFFIX}"
        try:
            with self._get_redis_connection() as redis_conn:
                serialized_messages = [serialize_message(msg) for msg in messages]
                self.logger.debug(
                    {
                        "message": f"Storing the chat_history with session_id: {session_id}",
                        "data": serialized_messages,
                    }
                )

                pipe = redis_conn.pipeline()
                pipe.rpush(key, *serialized_messages)
                pipe.expire(key, self.expiration)  # set expiration
                pipe.execute()
        except redis.exceptions.RedisError as e:
            self.logger.error(
                {
                    "message": f"Failed to store chat message for {session_id}",
                    "data": messages,
                    "error": e,
                }
            )

    def get_chat_history(self, session_id):
        key = f"{SESSION_KEY_PREFIX}{session_id}{CHAT_HISTORY_KEY_SUFFIX}"

        try:
            with self._get_redis_connection() as redis_conn:
                self.logger.debug({"message": "Retrieving the chat_history"})
                start = time.perf_counter()
                pipe = redis_conn.pipeline()

                pipe.lrange(key, 0, -1)
                pipe.expire(key, self.expiration)  # set expiration
                results = pipe.execute()
                chat_retrieval_time = time.perf_counter() - start
                deserialize_messages = [deserialize_message(msg) for msg in results[0]]
                self.logger.debug(
                    {
                        "message": "Successfull retrival of the chat_history",
                        "data": {
                            "deserialize_messages": deserialize_messages,
                            "chat_retrieval_time": chat_retrieval_time,
                        },
                    }
                )

                return deserialize_messages

        except redis.exceptions.RedisError as e:
            self.logger.error(
                {"message": f"Failed to get chat history for {session_id}", "error": e}
            )
            return []

    def acquire_lock(self, lock_name, acquire_timeout=10, lock_timeout=10):
        lock_key = f"lock:{lock_name}"
        lock_value = str(time.time())
        end_time = time.time() + acquire_timeout

        with self._get_redis_connection() as redis_conn:
            while time.time() < end_time:
                if redis_conn.set(lock_key, lock_value, nx=True, ex=lock_timeout):
                    return True  # Lock acquired
                time.sleep(0.1)  # Retry after a short delay
            return False  # Lock acquisition timed out

    def release_lock(self, lock_name):
        lock_key = f"lock:{lock_name}"
        with self._get_redis_connection() as redis_conn:
            redis_conn.delete(lock_key)

    def increment_counter(self, counter_name):
        try:
            with self._get_redis_connection() as redis_conn:
                return redis_conn.incr(counter_name)
        except redis.exceptions.RedisError as e:
            self.logger.error({"message": "Redis INCR error:", "error": e})

    def perform_atomic_operation(self, session_id, new_data):
        key = f"{SESSION_KEY_PREFIX}{session_id}"
        try:
            with self._get_redis_connection() as redis_conn:
                pipe = redis_conn.pipeline()
                pipe.set(key, json.dumps(new_data))
                pipe.expire(key, 3600)
                pipe.execute()
        except redis.exceptions.RedisError as e:
            self.logger.error({"message": "Redis atomic operation error", "error": e})

    def update_session_data(self, session_id: str, update_data: Dict) -> Optional[Dict]:
        try:
            session_data = self.get_session(session_id)
            if session_data:
                session_data.update(update_data)
                self.set_session(session_id, session_data)
                return session_data
            else:
                return None
        except redis.exceptions.RedisError as e:
            self.logger.error(
                {
                    "message": f"Failed to update session data for {session_id}: {e}",
                    "error": e,
                }
            )
            return None

    def close(self):
        """Closes the Redis connection pool."""
        if self.redis_pool:
            self.redis_pool.close()
            self.logger.info({"message": "Redis connection pool closed."})
