"""
DevOps Info Service
Main application module using FastAPI with JSON structured logging.
"""
import os
import socket
import platform
import logging
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any
from threading import Lock
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# JSON structured logging
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()
        log_record["level"] = record.levelname
        if record.name:
            log_record["logger"] = record.name
        if hasattr(record, "method"):
            log_record["method"] = record.method
        if hasattr(record, "path"):
            log_record["path"] = record.path
        if hasattr(record, "status_code"):
            log_record["status_code"] = record.status_code
        if hasattr(record, "client_ip"):
            log_record["client_ip"] = record.client_ip

log_handler = logging.StreamHandler()
log_handler.setFormatter(CustomJsonFormatter("%(message)s"))
logging.root.handlers = [log_handler]
logging.root.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DevOps Info Service",
    description="DevOps course info service",
    version="1.0.0"
)

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
DATA_DIR = os.getenv('DATA_DIR', '/data')
VISITS_FILE = Path(DATA_DIR) / "visits"
VISITS_LOCK = Lock()

# Application start time
START_TIME = datetime.now(timezone.utc)


# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)

devops_info_endpoint_calls = Counter(
    "devops_info_endpoint_calls",
    "DevOps info service endpoint calls",
    ["endpoint"],
)

devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "System info collection time in seconds",
)


def _endpoint_label(request: Request) -> str:
    try:
        return str(request.url.path)
    except Exception:
        return "unknown"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log each request and response in structured JSON."""

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = str(request.url.path)

        extra = {"method": method, "path": path, "client_ip": client_ip}
        logger.info("Request started", extra=extra)

        response = await call_next(request)
        status_code = response.status_code

        level = logging.ERROR if status_code >= 500 else (logging.WARNING if status_code >= 400 else logging.INFO)
        log_extra = {"method": method, "path": path, "status_code": status_code, "client_ip": client_ip}
        logger.log(level, "Request completed", extra=log_extra)

        return response


app.add_middleware(RequestLoggingMiddleware)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        endpoint = _endpoint_label(request)

        start = time.perf_counter()
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.perf_counter() - start
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
            http_requests_total.labels(
                method=method, endpoint=endpoint, status_code=str(status_code)
            ).inc()
            http_request_duration_seconds.labels(
                method=method, endpoint=endpoint, status_code=str(status_code)
            ).observe(duration)


app.add_middleware(PrometheusMetricsMiddleware)


def get_system_info() -> Dict[str, Any]:
    """Collect system information"""
    start = time.perf_counter()
    try:
        platform_info = platform.platform()
    except Exception:
        platform_info = platform.system()

    info = {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform_info,
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count() or 0,
        'python_version': platform.python_version()
    }
    devops_info_system_collection_seconds.observe(time.perf_counter() - start)
    return info


def get_uptime() -> Dict[str, Any]:
    """Calculate application uptime"""
    delta = datetime.now(timezone.utc) - START_TIME
    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    return {
        'seconds': total_seconds,
        'human': f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"}


def read_visits() -> int:
    if not VISITS_FILE.exists():
        return 0
    content = VISITS_FILE.read_text(encoding="utf-8").strip()
    if not content:
        return 0
    return int(content)


def write_visits(count: int) -> None:
    VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = VISITS_FILE.with_suffix(".tmp")
    tmp_file.write_text(str(count), encoding="utf-8")
    tmp_file.replace(VISITS_FILE)


def increment_visits() -> int:
    with VISITS_LOCK:
        count = read_visits() + 1
        write_visits(count)
        return count


@app.get("/")
async def index(request: Request) -> Dict[str, Any]:
    """Main endpoint - service and system information"""
    devops_info_endpoint_calls.labels(endpoint="/").inc()
    increment_visits()
    uptime = get_uptime()

    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Get user agent
    user_agent = request.headers.get('user-agent', 'unknown')

    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI"
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime['seconds'],
            "uptime_human": uptime['human'],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC"
        },
        "request": {
            "client_ip": client_ip,
            "user_agent": user_agent,
            "method": request.method,
            "path": str(request.url.path)
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Visits counter"}
        ]
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint for monitoring"""
    devops_info_endpoint_calls.labels(endpoint="/health").inc()
    uptime = get_uptime()

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime['seconds']
    }


@app.get("/visits")
async def visits() -> Dict[str, int]:
    devops_info_endpoint_calls.labels(endpoint="/visits").inc()
    with VISITS_LOCK:
        count = read_visits()
    return {"visits": count}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    logger.warning(
        "Not found",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown",
            "status_code": 404,
        }
    )
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "Endpoint does not exist"
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    logger.error(
        f"Internal server error: {exc}",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown",
            "status_code": 500,
        }
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    logger.info(
        "Starting DevOps Info Service",
        extra={
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
        }
    )
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info" if not DEBUG else "debug"
    )
