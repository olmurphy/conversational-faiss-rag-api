from prometheus_client import Counter, Histogram, Gauge, generate_latest
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
REQUEST_SIZE = Histogram(
    'http_request_size_bytes', 'HTTP Request Size', ['method', 'endpoint']
)
RESPONSE_SIZE = Histogram(
    'http_response_size_bytes', 'HTTP Response Size', ['method', 'endpoint']
)
IN_PROGRESS = Gauge(
    'http_requests_in_progress', 'Number of HTTP Requests in Progress', ['method', 'endpoint']
)

CPU_USAGE = Gauge('cpu_usage_percent', 'CPU Usage Percentage')
MEMORY_USAGE = Gauge('memory_usage_percent', 'Memory Usage Percentage')

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        endpoint = request.url.path
        start_time = time.time()
        IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()

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
            REQUEST_SIZE.labels(method=method, endpoint=endpoint).observe(request_size)
            RESPONSE_SIZE.labels(method=method, endpoint=endpoint).observe(response_size)
            IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()

            # Update CPU and memory usage metrics
            CPU_USAGE.set(psutil.cpu_percent())
            MEMORY_USAGE.set(psutil.virtual_memory().percent)

        return response