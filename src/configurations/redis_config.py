# src/configuration/redis_config.py
import redis
import urllib.parse
import ssl
from logging import Logger
import base64
import tempfile

FALLBACK_PORT: int = 6379
DEFAULT_MAX_CONNECTIONS = 10


class RedisConfig:
    def __init__(
        self,
        redis_url=None,
        redis_cert_path=None,
        logger=None,
        max_connections=DEFAULT_MAX_CONNECTIONS,
    ):
        self.redis_url = redis_url
        self.redis_cert_path = redis_cert_path
        self.logger: Logger = logger
        self._redis_client = None  # Lazy initialization
        self.max_connections = max_connections

    def _create_redis_client(self):
        if not self.redis_url:
            self.logger.error({"message": "No Redis URL supplied"})
            return None
        try:
            parsed_url = urllib.parse.urlparse(self.redis_url)
            host = parsed_url.hostname
            port = parsed_url.port or FALLBACK_PORT  # Default Redis port
            db = (
                int(parsed_url.path.strip("/")) if parsed_url.path else 0
            )  # get the index from the url
            password = parsed_url.password
            username = parsed_url.username  # get the username

            self.logger.debug(
                {
                    "message": "Redis client created",
                    "data": {
                        "host": host,
                        "port": port,
                        "db": db,
                        "cert_path": self.redis_cert_path,
                        "username": username,
                        "password": password,
                    },
                }
            )  # logging for debugging

            with open(self.redis_cert_path, "r") as f:
                encoded_cert = f.read()
            decoded_cert = base64.b64decode(encoded_cert).decode("utf-8")

            with tempfile.NamedTemporaryFile(delete=False) as temp_cert_file:
                temp_cert_file.write(decoded_cert.encode("utf-8"))
                temp_cert_path = temp_cert_file.name

            redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                decode_responses=True,
                max_connections=self.max_connections,
                ssl_ca_certs=temp_cert_path,
                ssl_cert_reqs="required",
            )
            return redis_pool
        except (redis.exceptions.ConnectionError, ValueError) as e:
            self.logger.error(
                {
                    "message": "Error connecting to Redis Instance",
                    "data": {"host": host, "port": port, db: db, "cert_path": self.redis_cert_path,},
                    "error": e,
                }
            )  # logging for error.

            return None

    def get_redis_client(self):
        if self._redis_client is None:
            self._redis_client = self._create_redis_client()
        return self._redis_client

    def check_health(self) -> bool:
        """Checks if the Redis connection is healthy."""
        redis_pool = self.get_redis_client()
        if not redis_pool:
            return False
        try:
            with redis.Redis(connection_pool=redis_pool) as redis_client:
                return redis_client.ping()  # Pings the Redis server
        except redis.exceptions.RedisError as e:
            self.logger.error({"message": "Redis health check failed", "error": str(e)})
            return False