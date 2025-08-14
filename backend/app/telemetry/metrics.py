<file>
      <absolute_file_name>/app/backend/app/telemetry/metrics.py</absolute_file_name>
      <content">from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from fastapi.routing import APIRoute
from typing import Callable
import time

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP requests', 
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds', 
    'HTTP request duration', 
    ['method', 'endpoint']
)

WEBHOOK_EVENTS = Counter(
    'webhook_events_total',
    'Total webhook events received',
    ['source', 'event_type']
)

WORKER_PROCESSED = Counter(
    'worker_events_processed_total',
    'Total events processed by worker',
    ['status']
)

AI_REQUESTS = Counter(
    'ai_requests_total',
    'Total AI API requests',
    ['model', 'function']
)

JIRA_API_CALLS = Counter(
    'jira_api_calls_total',
    'Total Jira API calls',
    ['endpoint', 'status']
)

class MetricsMiddleware:
    """Middleware to collect HTTP metrics"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        method = scope["method"]
        path = scope["path"]
        
        # Find matching route for cleaner metrics
        endpoint = path
        for route in scope.get("route", []):
            if hasattr(route, 'path'):
                endpoint = route.path
                break
        
        status_code = 200
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
        
        # Record metrics
        duration = time.time() - start_time
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

def get_metrics() -> Response:
    """Endpoint to expose Prometheus metrics"""
    metrics_data = generate_latest()
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)

# Helper functions for recording metrics
def record_webhook_event(source: str, event_type: str):
    """Record webhook event metric"""
    WEBHOOK_EVENTS.labels(source=source, event_type=event_type).inc()

def record_worker_processed(status: str):
    """Record worker processed event metric"""
    WORKER_PROCESSED.labels(status=status).inc()

def record_ai_request(model: str, function: str):
    """Record AI API request metric"""
    AI_REQUESTS.labels(model=model, function=function).inc()

def record_jira_api_call(endpoint: str, status: str):
    """Record Jira API call metric"""
    JIRA_API_CALLS.labels(endpoint=endpoint, status=status).inc()
</content>
    </file>