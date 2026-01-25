"""
DevOps Info Service
Main application module using FastAPI
"""
import os
import socket
import platform
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        'human': f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    }


@app.get("/")
async def index(request: Request) -> Dict[str, Any]:
    """Main endpoint - service and system information"""
    logger.info(f"Request: {request.method} {request.url.path}")
    
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
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    logger.info(f"Starting DevOps Info Service on {HOST}:{PORT}")
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info" if not DEBUG else "debug"
    )