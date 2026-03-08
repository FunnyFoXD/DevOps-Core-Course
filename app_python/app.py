"""
DevOps Info Service
Main application module using FastAPI with JSON structured logging.
"""
import os
import socket
import platform
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

from pythonjsonlogger import jsonlogger

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

# Application start time
START_TIME = datetime.now(timezone.utc)


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


def get_system_info() -> Dict[str, Any]:
    """Collect system information"""
    try:
        platform_info = platform.platform()
    except Exception:
        platform_info = platform.system()

    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform_info,
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count() or 0,
        'python_version': platform.python_version()
    }


def get_uptime() -> Dict[str, Any]:
    """Calculate application uptime"""
    delta = datetime.now(timezone.utc) - START_TIME
    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    return {
        'seconds': total_seconds,
        'human': f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"}


@app.get("/")
async def index(request: Request) -> Dict[str, Any]:
    """Main endpoint - service and system information"""
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
            {"path": "/health", "method": "GET", "description": "Health check"}
        ]
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint for monitoring"""
    uptime = get_uptime()

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime['seconds']
    }


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
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info" if not DEBUG else "debug"
    )
