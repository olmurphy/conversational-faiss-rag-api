from prometheus_client import (Counter, Gauge, Histogram, Summary,
                               generate_latest)
from fastapi import Response


class MetricsManager:
    def __init__(self, namespace="my_app"):
        self.namespace = namespace
        # HTTP Request Metrics
        self.requests_total = Counter(
            "http_requests_total",
            "Total number of HTTP requests",
            ["method", "endpoint", "status", "error_type"],
            namespace=self.namespace,
        )
        self.request_latency = Histogram(
            "http_request_latency_seconds",
            "HTTP request latency in seconds",
            ["method", "endpoint"],
            namespace=self.namespace,
        )

        # RAG-Specific Metrics
        self.faiss_retrieval_latency = Histogram(
            "faiss_retrieval_latency_seconds",
            "FAISS retrieval latency in seconds",
            ["index_name"],
            namespace=self.namespace,
        )
        self.faiss_retrieval_results = Histogram(
            "faiss_retrieval_results",
            "Number of documents retrieved from FAISS",
            ["index_name"],
            namespace=self.namespace,
        )
        self.faiss_retrieval_error = Counter(
            "faiss_retrieval_errors_total",
            "Count of FAISS retrieval errors",
            ["index_name", "error_type"],
            namespace=self.namespace,
        )
        self.document_aggregation_latency = Histogram(
            "document_aggregation_latency_seconds",
            "Document aggregation latency in seconds",
            namespace=self.namespace,
        )
        self.document_aggregation_size = Histogram(
            "document_aggregation_size",
            "Size of aggregated documents (tokens/characters)",
            namespace=self.namespace,
        )
        self.input_tokens = Histogram(
            "input_tokens",
            "Number of tokens in the user's input",
            namespace=self.namespace,
        )
        self.retrieved_documents_tokens = Histogram(
            "retrieved_documents_tokens",
            "Number of tokens in the retrieved documents",
            namespace=self.namespace,
        )
        self.chat_history_tokens = Histogram(
            "chat_history_tokens",
            "Number of tokens in the chat history",
            namespace=self.namespace,
        )
        self.output_tokens = Histogram(
            "output_tokens",
            "Number of tokens in the LLM's output",
            namespace=self.namespace,
        )
        self.token_limit_exceeded = Counter(
            "token_limit_exceeded_total",
            "Count of instances where token limits were exceeded",
            ["limit_type"],
            namespace=self.namespace,
        )
        self.llm_invocation_latency = Histogram(
            "llm_invocation_latency_seconds",
            "LLM invocation latency in seconds",
            ["model"],
            namespace=self.namespace,
        )
        self.llm_invocation_errors = Counter(
            "llm_invocation_errors_total",
            "Count of LLM invocation errors",
            ["model", "error_type"],
            namespace=self.namespace,
        )
        self.llm_completion_length = Histogram(
            "llm_completion_length",
            "Length of LLM completions (in tokens)",
            ["model"],
            namespace=self.namespace,
        )
        self.rag_pipeline_step_latency = Histogram(
            "rag_pipeline_step_latency_seconds",
            "Latency of each step of the RAG pipeline",
            ["step_name"],
            namespace=self.namespace,
        )

        # Data Store Metrics (Redis and PostgreSQL)
        self.redis_get_latency = Histogram(
            "redis_get_latency_seconds",
            "Redis GET operation latency in seconds",
            namespace=self.namespace,
        )
        self.redis_set_latency = Histogram(
            "redis_set_latency_seconds",
            "Redis SET operation latency in seconds",
            namespace=self.namespace,
        )
        self.redis_errors = Counter(
            "redis_errors_total",
            "Count of Redis errors",
            ["operation", "error_type"],
            namespace=self.namespace,
        )
        self.redis_connection_errors = Counter(
            "redis_connection_errors_total",
            "Count of redis connection errors",
            namespace=self.namespace,
        )
        self.postgres_query_latency = Histogram(
            "postgres_query_latency_seconds",
            "PostgreSQL query latency in seconds",
            ["query_type", "table_name"],
            namespace=self.namespace,
        )
        self.postgres_query_errors = Counter(
            "postgres_query_errors_total",
            "Count of PostgreSQL query errors",
            ["query_type", "table_name", "error_type"],
            namespace=self.namespace,
        )
        self.postgres_connection_errors = Counter(
            "postgres_connection_errors_total",
            "Count of Postgres connection errors",
            namespace=self.namespace,
        )
        self.cache_hits = Counter(
            "cache_hits_total",
            "Number of cache hits",
            ["cache_type"],
            namespace=self.namespace,
        )
        self.cache_misses = Counter(
            "cache_misses_total",
            "Number of cache misses",
            ["cache_type"],
            namespace=self.namespace,
        )

        # Background Task Metrics
        self.background_task_latency = Histogram(
            "background_task_latency_seconds",
            "Latency of background tasks in seconds",
            ["task_name"],
            namespace=self.namespace,
        )
        self.background_task_errors = Counter(
            "background_task_errors_total",
            "Count of background task errors",
            ["task_name", "error_type"],
            namespace=self.namespace,
        )
        self.background_task_queue_size = Gauge(
            "background_task_queue_size",
            "Current size of the background task queue",
            namespace=self.namespace,
        )

        # Application-Specific Metrics
        self.active_user_sessions = Gauge(
            "active_user_sessions",
            "Number of currently active user sessions",
            namespace=self.namespace,
        )
        self.user_feedback = Counter(
            "user_feedback_total",
            "Count of user feedback",
            ["feedback_type"],
            namespace=self.namespace,
        )
        self.conversation_length = Histogram(
            "conversation_length",
            "Length of user conversations (in turns)",
            namespace=self.namespace,
        )
        self.session_timeouts = Counter(
            "session_timeouts_total",
            "Count of user session timeouts",
            namespace=self.namespace,
        )
        self.llm_token_usage = Counter(
            "llm_token_usage_total",
            "Total LLM token usage",
            ["model", "type"],
            namespace=self.namespace,
        )
        self.database_query_latency = Summary(
            "database_query_latency_seconds",
            "Database query latency in seconds",
            ["query_type"],
            namespace=self.namespace,
        )

    def expose_metrics(self) -> Response:
        metrics_data = generate_latest()
        return Response(content=metrics_data, media_type="text/plain")
