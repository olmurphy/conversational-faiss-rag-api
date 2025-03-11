import base64
import logging
import os
import ssl
import tempfile
from urllib.parse import urlparse

from sqlalchemy.engine.url import URL
from configurations.service_model import PostgresDB



class PostgresDBConfig:
    def __init__(
        self,
        db,
        host,
        password,
        port,
        user,
        ssl_ca_cert_path=None,
        postgres_pool_config: PostgresDB = None,
        logger: logging.Logger=None,
    ):
        self.db = db
        self.host = host
        self.password = password
        self.port = port
        self.user = user
        self.pool_size = postgres_pool_config.pool_size
        self.max_overflow = postgres_pool_config.max_overflow
        self.pool_recycle = postgres_pool_config.pool_recycle
        self.ssl_ca_cert_path = ssl_ca_cert_path
        self.logger = logger or logging.getLogger(__name__)

        self.parsed_url = self._create_url()
        self._validate_url()

    def _create_url(self, ):
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.db,
        )


    def _validate_url(self):
        parsed = urlparse(str(self.parsed_url)) #parse the string representation of the url.
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid database URL format.")

    def get_sqlalchemy_url(self):
        return self.parsed_url

    def get_connection_pool_options(self):
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_recycle": self.pool_recycle,
        }

    # def get_ssl_context(self):
    #     if not self.ssl_ca_cert_path:
    #         return None  # SSL not configured

    #     try:
    #         with open(self.ssl_ca_cert_path, "r") as f:
    #             encoded_cert = f.read()

    #         decoded_cert = base64.b64decode(encoded_cert).decode("utf-8")

    #         with tempfile.NamedTemporaryFile(delete=False, mode="w") as temp_cert_file:
    #             temp_cert_file.write(decoded_cert)
    #             temp_cert_path = temp_cert_file.name

    #         ssl_context = ssl.create_default_context(cafile=temp_cert_path)
    #         return ssl_context
    #     except FileNotFoundError:
    #         self.logger.error(
    #             f"SSL CA certificate file not found: {self.ssl_ca_cert_path}"
    #         )
    #         return None
    #     except base64.binascii.Error:
    #         self.logger.error("Invalid base64 encoded certificate in file.")
    #         return None
    #     except Exception as e:
    #         self.logger.error(f"Error creating SSL context: {e}")
    #         return None

    def __repr__(self):
        return (
            f"DatabaseConfig("
            f"db='{self.db}', "
            f"host='{self.host}', "
            f"port={self.port}, "
            f"user='{self.user}', "
            f"pool_size={self.pool_size}, "
            f"max_overflow={self.max_overflow}, "
            f"pool_recycle={self.pool_recycle}, "
            f"ssl_ca_cert_path='{self.ssl_ca_cert_path}'"
            f")"
        )
