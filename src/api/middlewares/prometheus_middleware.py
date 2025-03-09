from prometheus_client import Counter, Histogram, Gauge, Summary
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
import psutil

REQUEST_COUNT = Counter(
    'http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'http_status']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint']
)
REQUEST_LATENCY_PERCENTILES = Histogram(
    'http_request_latency_percentiles', 'HTTP Request Latency Percentiles', ['method', 'endpoint'], buckets=(0.1, 0.5, 0.9, 0.95, 0.99)
)
REQUEST_SIZE = Histogram(
    'http_request_size_bytes', 'HTTP Request Size', ['method', 'endpoint']
)
RESPONSE_SIZE = Histogram(
    'http_response_size_bytes', 'HTTP Response Size', ['method', 'endpoint']
)
IN_PROGRESS = Gauge(
    'http_requests_in_progress', 'Number of HTTP Requests in Progress', ['method', 'endpoint']
)
DB_QUERY_COUNT = Counter(
    'db_query_count', 'Number of Database Queries Executed', ['method', 'endpoint']
)
DB_QUERY_DURATION = Summary(
    'db_query_duration_seconds', 'Database Query Duration', ['method', 'endpoint']
)
SLOW_QUERIES = Counter(
    'slow_queries', 'Number of Slow Database Queries', ['method', 'endpoint']
)
CACHE_HIT_RATE = Counter(
    'cache_hit_rate', 'Cache Hit Rate', ['method', 'endpoint']
)
CACHE_MISS_RATE = Counter(
    'cache_miss_rate', 'Cache Miss Rate', ['method', 'endpoint']
)
CACHE_HIT_LATENCY = Summary(
    'cache_hit_latency_seconds', 'Cache Hit Latency', ['method', 'endpoint']
)
CACHE_MISS_LATENCY = Summary(
    'cache_miss_latency_seconds', 'Cache Miss Latency', ['method', 'endpoint']
)
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU Usage Percentage')
MEMORY_USAGE = Gauge('memory_usage_percent', 'Memory Usage Percentage')
THREAD_COUNT = Gauge('thread_count', 'Number of Threads')
GC_EVENTS = Counter('gc_events_total', 'Total Garbage Collection Events')
GC_TIME = Summary('gc_time_seconds', 'Time Spent in Garbage Collection')
REQUEST_CONCURRENCY = Gauge('request_concurrency', 'Number of Concurrent Requests')
REQUEST_TIMEOUTS = Counter('request_timeouts', 'Number of Request Timeouts')
REQUEST_RETRIES = Counter('request_retries', 'Number of Request Retries')
DB_CONNECTION_POOL_USAGE = Gauge('db_connection_pool_usage', 'Database Connection Pool Usage', ['state'])
CACHE_EVICTIONS = Counter('cache_evictions', 'Number of Cache Evictions')
CACHE_EXPIRATIONS = Counter('cache_expirations', 'Number of Cache Expirations')
QUEUE_LENGTH = Gauge('queue_length', 'Length of Internal Queues', ['queue_name'])
QUEUE_PROCESSING_TIME = Summary('queue_processing_time_seconds', 'Queue Processing Time', ['queue_name'])
EXTERNAL_API_CALL_COUNT = Counter('external_api_call_count', 'Number of External API Calls', ['api_name'])
EXTERNAL_API_CALL_DURATION = Summary('external_api_call_duration_seconds', 'External API Call Duration', ['api_name'])
DISK_IO = Counter('disk_io_operations', 'Disk I/O Operations', ['operation'])
DISK_SPACE_USAGE = Gauge('disk_space_usage_bytes', 'Disk Space Usage', ['path'])
NETWORK_IO = Counter('network_io_operations', 'Network I/O Operations', ['operation'])
NETWORK_LATENCY = Summary('network_latency_seconds', 'Network Latency', ['operation'])
THREAD_POOL_USAGE = Gauge('thread_pool_usage', 'Thread Pool Usage', ['state'])
THREAD_POOL_QUEUE_SIZE = Gauge('thread_pool_queue_size', 'Thread Pool Queue Size')
THREAD_POOL_TASK_DURATION = Summary('thread_pool_task_duration_seconds', 'Thread Pool Task Duration')
ERROR_DETAILS = Counter('error_details', 'Detailed Error Breakdown', ['error_type'])
SERVICE_UPTIME = Gauge('service_uptime_seconds', 'Service Uptime')
SERVICE_RESTART_COUNT = Counter('service_restart_count', 'Number of Service Restarts')
CONFIGURATION_CHANGES = Counter('configuration_changes', 'Number of Configuration Changes')
DEPLOYMENT_COUNT = Counter('deployment_count', 'Number of Deployments')
DEPLOYMENT_SUCCESS = Counter('deployment_success', 'Number of Successful Deployments')
DEPLOYMENT_FAILURE = Counter('deployment_failure', 'Number of Failed Deployments')
FEATURE_USAGE = Counter('feature_usage', 'Feature Usage', ['feature_name'])
FEATURE_TOGGLE_USAGE = Counter('feature_toggle_usage', 'Feature Toggle Usage', ['toggle_name'])
USER_LOGIN_EVENTS = Counter('user_login_events', 'Number of User Login Events')
USER_LOGOUT_EVENTS = Counter('user_logout_events', 'Number of User Logout Events')
SESSION_START_EVENTS = Counter('session_start_events', 'Number of Session Start Events')
SESSION_END_EVENTS = Counter('session_end_events', 'Number of Session End Events')
API_RATE_LIMITING = Counter('api_rate_limiting', 'Number of API Rate Limiting Events')
THROTTLING_EVENTS = Counter('throttling_events', 'Number of Throttling Events')
CIRCUIT_BREAKER_EVENTS = Counter('circuit_breaker_events', 'Number of Circuit Breaker Events')
DEPENDENCY_HEALTH = Gauge('dependency_health', 'Health of External Dependencies', ['dependency'])
SERVICE_AVAILABILITY = Gauge('service_availability', 'Service Availability')
ACTIVE_USERS = Gauge('active_users', 'Number of Active Users')
SESSION_DURATION = Summary('session_duration_seconds', 'User Session Duration')

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        endpoint = request.url.path
        start_time = time.time()
        IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
        REQUEST_CONCURRENCY.inc()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            duration = time.time() - start_time
            request_size = len(await request.body())
            response_size = 1

            REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=status_code).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
            REQUEST_LATENCY_PERCENTILES.labels(method=method, endpoint=endpoint).observe(duration)
            REQUEST_SIZE.labels(method=method, endpoint=endpoint).observe(request_size)
            RESPONSE_SIZE.labels(method=method, endpoint=endpoint).observe(response_size)
            IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()
            REQUEST_CONCURRENCY.dec()

            # Update additional metrics
            CPU_USAGE.set(psutil.cpu_percent())
            MEMORY_USAGE.set(psutil.virtual_memory().percent)
            THREAD_COUNT.set(psutil.cpu_count())
            # Simulate DB query metrics
            DB_QUERY_COUNT.labels(method=method, endpoint=endpoint).inc()
            DB_QUERY_DURATION.labels(method=method, endpoint=endpoint).observe(duration / 2)  # Example value
            SLOW_QUERIES.labels(method=method, endpoint=endpoint).inc()  # Example value
            # Simulate cache metrics
            CACHE_HIT_RATE.labels(method=method, endpoint=endpoint).inc()
            CACHE_MISS_RATE.labels(method=method, endpoint=endpoint).inc()
            CACHE_HIT_LATENCY.labels(method=method, endpoint=endpoint).observe(duration / 3)  # Example value
            CACHE_MISS_LATENCY.labels(method=method, endpoint=endpoint).observe(duration / 4)  # Example value

            # Simulate other metrics
            DB_CONNECTION_POOL_USAGE.labels(state='active').set(10)  # Example value
            DB_CONNECTION_POOL_USAGE.labels(state='idle').set(5)  # Example value
            CACHE_EVICTIONS.inc()
            CACHE_EXPIRATIONS.inc()
            QUEUE_LENGTH.labels(queue_name='example_queue').set(5)  # Example value
            QUEUE_PROCESSING_TIME.labels(queue_name='example_queue').observe(duration / 3)  # Example value
            EXTERNAL_API_CALL_COUNT.labels(api_name='example_api').inc()
            EXTERNAL_API_CALL_DURATION.labels(api_name='example_api').observe(duration / 4)  # Example value
            DISK_IO.labels(operation='read').inc()
            DISK_IO.labels(operation='write').inc()
            DISK_SPACE_USAGE.labels(path='/').set(1000000000)  # Example value
            NETWORK_IO.labels(operation='send').inc()
            NETWORK_IO.labels(operation='receive').inc()
            NETWORK_LATENCY.labels(operation='send').observe(duration / 5)  # Example value
            NETWORK_LATENCY.labels(operation='receive').observe(duration / 6)  # Example value
            THREAD_POOL_USAGE.labels(state='active').set(20)  # Example value
            THREAD_POOL_USAGE.labels(state='idle').set(10)  # Example value
            THREAD_POOL_QUEUE_SIZE.set(5)  # Example value
            THREAD_POOL_TASK_DURATION.observe(duration / 7)  # Example value
            ERROR_DETAILS.labels(error_type='example_error').inc()
            SERVICE_UPTIME.set(time.time() - start_time)  # Example value
            SERVICE_RESTART_COUNT.inc()
            CONFIGURATION_CHANGES.inc()
            DEPLOYMENT_COUNT.inc()
            DEPLOYMENT_SUCCESS.inc()
            DEPLOYMENT_FAILURE.inc()
            FEATURE_USAGE.labels(feature_name='example_feature').inc()
            FEATURE_TOGGLE_USAGE.labels(toggle_name='example_toggle').inc()
            USER_LOGIN_EVENTS.inc()
            USER_LOGOUT_EVENTS.inc()
            SESSION_START_EVENTS.inc()
            SESSION_END_EVENTS.inc()
            API_RATE_LIMITING.inc()
            THROTTLING_EVENTS.inc()
            CIRCUIT_BREAKER_EVENTS.inc()
            DEPENDENCY_HEALTH.labels(dependency='example_dependency').set(1)  # Example value
            SERVICE_AVAILABILITY.set(99.99)  # Example value
            ACTIVE_USERS.set(100)  # Example value
            SESSION_DURATION.observe(duration / 5)  # Example value

        return response