import json

import redis
import requests
from configurations.redis_config import RedisConfig
from fastapi import HTTPException


class RedisAuth:
    def __init__(self, redis_config: RedisConfig, expiration=3600):
        self.redis_pool = redis_config.get_redis_client()
        self.logger = redis_config.logger
        self.expiration = expiration

        if not self.redis_pool:
            raise ValueError("Redis client for JWKS Cache initialization failed")
        self.logger.info({"message": "JWKS Cache initialized successfully."})

    def _get_redis_connection(self):
        return redis.Redis(connection_pool=self.redis_pool)

    def get_jwks(self, jwks_url: str):
        """
        Fetches JWKS from the given URL and caches it in Redis.

        Args:
            jwks_url: The URL to fetch the JWKS.
            redis_conn: redis connection object.

        Returns:
            The JWKS as a dictionary.
        """
        try:
            with self._get_redis_connection() as redis_conn:
                cached_jwks = redis_conn.get(jwks_url)
                if cached_jwks:
                    return json.loads(cached_jwks)

                return self.get_jwks_from_url(jwks_url=jwks_url, redis_conn=redis_conn)
        except redis.exceptions.RedisError as e:
            self.logger.error({"message": "Failed to get the jwks_url", "error": e})

    def get_jwks_from_url(self, jwks_url, redis_conn):
        """
        Fetches JWKS from the given URL and caches it in Redis.

        Args:
            jwks_url: The URL to fetch the JWKS.
            redis_conn: redis connection object.

        Returns:
            The JWKS as a dictionary.
        """
        try:
            response = requests.get(jwks_url)
            response.raise_for_status()
            jwks = response.json()
            redis_conn.setex(
                jwks_url, self.expiration, json.dumps(jwks)
            )  # Cache for 1 hour

            return jwks
        except requests.exceptions.RequestException as e:
            self.logger.error(
                {"message": "Error fetching JWKS from {jwks_url}", "error": e}
            )
            raise HTTPException(status_code=500, detail="Failed to retrieve JWKS.")

    def get_access_token(self, session_id: str):
        """
        Retrieves the access token associated with a session ID from Redis.

        Args:
            session_id: The session ID.

        Returns:
            The access token, or None if not found.
        """
        try:
            with self._get_redis_connection() as redis_conn:
                session_data = redis_conn.get("chat-widget_dev_" + session_id)
                if session_data:
                    session_dict = json.loads(session_data)
                    return session_dict.get("accessToken")
                return None
        except redis.exceptions.RedisError as e:
            self.logger.error(
                {
                    "message": f"Failed to get access token for session {session_id}",
                    "error": e,
                }
            )
            raise HTTPException(
                status_code=500, detail="Redis error while fetching access token."
            )

    def close(self):
        """Closes the Redis connection pool."""
        if self.redis_pool:
            self.redis_pool.close()
            self.logger.info({"message": "Redis connection pool closed."})