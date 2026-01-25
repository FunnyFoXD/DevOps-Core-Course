import uvicorn
import os
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# FastAPI app
app = FastAPI(
    title="DevOps Info Service",
    description="A service that provides information about the system it is running on",
    version="1.0.0",
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Start time
START_TIME = datetime.now(timezone.utc)

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Main function
if __name__ == "__main__":
    logger.info(f"Application starting on {HOST}:{PORT}")

    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info" if not DEBUG else "debug",
    )