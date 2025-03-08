from typing import Optional
from pydantic import BaseModel, Field


class Variables(BaseModel):
    PORT: Optional[int] = Field(
        8000,
        description='The port on which the application will run.'
    )
    LOG_LEVEL: Optional[str] = Field(
        'DEBUG',
        description='The logging level for the application.',
        json_schema_extra={
            "enum": ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        }
    )
    SERVICE_NAME: str = Field(
        description='Name of the service'
    )
    OPENAI_API_KEY: str = Field(
        description='The API key for accessing the Language Model API.'
    )
    OPENAI_BASE_URL: str = Field(
        description='The API URL for accessing the Language Model API.'
    )
    HEADERS_TO_PROXY: Optional[str] = Field(
        None,
        description='The headers to proxy from the client to the server during intra-service communication.'
    )
    CONFIGURATION_PATH: str = Field(
        description='configuration path for the specifications of the embeddings, llm, etc.'
    )
    SAMPLE_DATA_PATH: str = Field(
        description='file path to the sample data.csv to be ingested and embedded in the faiss vectorstore'
    )
    REDIS_URL: str = Field(
        description='connection string to the REDIS instance'
    )
    REDIS_CERT_PATH: str = Field(
        description='path to the redis cert'
    )
    PG_DB: str = Field(
        description='name of DB to connect to'
    )
    PG_HOST: str = Field(
        description='host url where postgres is served to connect to'
    )
    PG_PASSWORD: str = Field(
        description='password to connect to DB'
    )
    PG_PORT: int = Field(
        description='port of the DB to connect'
    )
    PG_USER: str = Field(
        description='user of the db used'
    )
    PG_CERT_BASE64: str = Field(
        description='path to the postgres cert'
    )