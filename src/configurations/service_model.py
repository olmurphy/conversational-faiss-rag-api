from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OpenAILlmConfiguration(BaseModel):
    type: str = Field(
        "openai",
        description="The type of language model to be used by AI RAG Template for natural language processing and understanding.",
    )
    name: str = Field(
        ...,
        description="The name of the language model (LLM) to be used. Check the OpenAI documentation for available models.",
    )
    temperature: Optional[float] = Field(
        0.7,
        description="The temperature parameter for sampling from the language model. A higher value increases the randomness of the generated text.",
    )
    tokenizer: str = Field(
        ...,
        description="the name of the tokenizer to use for counting tokens of text",
    )
    max_chat_history_tokens: int = Field(
        ...,
        description="max number of tokens of chat history to include in the LLM invoke call",
    )
    max_context_tokens: int = Field(
        ...,
        description="max number of tokens of context (doc context retrieval) to include in the LLM invoke call",
    )
    top_p: float = Field(
    ...,
    description="Nucleus sampling: cumulative probability threshold for token selection (0.0 to 1.0, higher = more diverse)."
    "Controls output diversity by selecting the most likely tokens until the cumulative probability exceeds this value.",
)



class EmbeddingsConfiguration(BaseModel):
    type: str = Field(
        "openai",
        description="The type of language model to be used by AI RAG Template for the embeddings generation.",
    )
    name: str = Field(
        ...,
        description="The name of the embeddings model to be used by RAG-template for various tasks such as text representation and similarity.",
    )
    normalize_embeddings: str = Field(
        ...,
        description="This is a boolean, True if want to normalize embeddings, False otherwise",
    )
    size: int = Field(
        ...,
        description= "Size of the vector embedding, dpends on the embedding model"
    ),
    nprobe: int = Field(
            ...,
            description= "Number of clusters to explorer at search time."
        )


class RelevanceScoreFn(Enum):
    euclidean = "euclidean"
    cosine = "cosine"
    dotProduct = "dotProduct"


class VectorStore(BaseModel):
    indexName: str = Field(
        ...,
        description="The name of the index to be used by RAG-template for various tasks such as text representation and similarity.",
    )
    relevanceScoreFn: Optional[RelevanceScoreFn] = Field(
        "euclidean",
        description="The function used to calculate relevance scores for vectors. Options: 'euclidean', 'cosine', 'dotProduct'.",
    )
    embeddingKey: str = Field(
        ..., description="The key used to identify embeddings in the vector store."
    )
    textKey: str = Field(
        ..., description="The key used to store text data in the vector store."
    )
    maxDocumentsToRetrieve: Optional[int] = Field(
        4,
        description="The maximum number of documents to be retrieved from the vector store.",
    )
    cutOffDistance: Optional[float] = Field(
        None, description="The maximum score distance for the vectors."
    )
    minScoreDistance: Optional[float] = Field(
        None, description="The min score distance for the vectors."
    )


class Cache(BaseModel):
    capacity: int = Field(
        ...,
        description="max capacity in the LRU cache",
    )
    expiry_time: int = Field(
        ...,
        description="TTL for items in the cache, otherwise evicted",
    )
    cleanup_interval: int = Field(
        ..., description="time to wait until check to clean up cache again"
    )


class Redis(BaseModel):
    time_to_live: int = Field(
        ...,
        description="TTL for each access of data in Redis",
    )
    max_connections: int = Field(
        ...,
        description="max number of connections in the pool",
    )
    polling_interval: int = Field(
        ...,
        description="number of seconds to wait before polling again",
    )


class PostgresDB(BaseModel):
    pool_size: int = Field(
        ...,
        description="Specifies the initial number of database connections maintained in the connection pool.",
    )
    max_overflow: int = Field(
        ...,
        description="Defines the maximum number of additional connections that can be created beyond the pool size when needed.",
    )
    pool_recycle: int = Field(
        ...,
        description="Sets the number of seconds a connection can remain idle before being recycled to prevent stale connections.",
    )


class ConfigSchema(BaseModel):
    llm: OpenAILlmConfiguration
    vectorStore: VectorStore
    embeddings: EmbeddingsConfiguration
    cache: Cache
    redis: Redis
    postgresDB: PostgresDB
