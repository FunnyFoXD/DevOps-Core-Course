# Lab 1 Submission - DevOps Info Service

## Framework Selection

### Choice: FastAPI

I chose **FastAPI** as the web framework for this project.

### Why FastAPI?

1. **Modern and Fast**: FastAPI is one of the fastest Python web frameworks

2. **Automatic API Documentation**: FastAPI automatically generates interactive API documentation (Swagger UI and ReDoc)

3. **Type Safety**: Built-in support for Python type hints and automatic request/response validation

4. **Async Support**: Native support for async/await makes it easy to write high-performance concurrent code

5. **Easy to Learn**: FastAPI has a simple, intuitive API that's easy to pick up

### Comparison with Alternatives

| Feature | FastAPI | Flask | Django |
|---------|---------|-------|--------|
| **Learning Curve** | Moderate | Easy | Steep |
| **Performance** | Very High | Moderate | Moderate |
| **Async Support** | Native | Limited | Native |
| **Auto Documentation** | Yes | No | Yes |
| **Type Validation** | Built-in | Manual | Built-in |
| **Size** | Lightweight | Lightweight | Full-featured |
| **Use Case** | APIs, Microservices | Small apps, APIs | Full web apps |
| **Best For** | Modern APIs, High performance | Simple apps, Learning | Complex web apps |

**Decision Rationale**: For a DevOps course focusing on APIs and microservices, FastAPI's performance, automatic documentation, and modern features make it the ideal choice

## Best Practices Applied

### 1. Clean Code Organization

**Implementation:**
- Clear, descriptive function names (`get_system_info()`, `get_uptime()`)
- Proper import grouping
- Docstrings for all functions explaining their purpose
- Minimal comments (code is self-documenting)
- PEP 8 compliant formatting (common style for all)

**Code Example:**
```python
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
```
**Importance**: Clean code is easier to maintain, debug, and extend. It reduces cognitive load and makes collaboration easier

### 2. Error Handling

**Implementation:**
- Custom exception handlers for 404 and 500 errors
- All errors return consistent JSON responses
- Error logging for debugging

**Code Example:**
```python
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
```
**Importance**: Proper error handling provides better user experience, helps with debugging, and prevents application crashes. Consistent error responses make API consumption easier

### 3. Logging

**Implementation:**
- Configured logging with appropriate level
- Structured log format with timestamps
- Logging important events

**Code Example:**
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info(f"Starting DevOps Info Service on {HOST}:{PORT}")
logger.info(f"Request: {request.method} {request.url.path}")
```
**Importance**: Logging is essential for debugging, monitoring, and understanding application behavior in production. It helps track issues and analyze usage patterns

### 4. Configuration Management

**Implementation:**
- Environment variables for configuration
- Sensible defaults
- No hardcoded values

**Code Example:**
```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```
**Importance**: Environment-based configuration allows the same code to run in different environments without code changes. This is a DevOps best practice

### 5. Type Hints

**Implementation:**
- Type hints for function parameters and return values
- Improves code readability and IDE support

**Code Example:**
```python
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
```
**Importance**: Type hints improve code documentation, enable better IDE autocomplete, and help catch errors early. They're especially valuable in FastAPI for automatic validation

### 6. Dependency Management

**Implementation:**
- Pinned exact versions in `requirements.txt`
- Reproducible builds

**Code Example:**
```txt
# Web Framework
fastapi==0.115.0
uvicorn[standard]==0.32.0
```
**Importance**: Pinning versions ensures consistent behavior across different environments and prevents unexpected breaking changes from dependency updates

## API Documentation

### Endpoint: `GET /`

**Description**: Returns comprehensive service and system information

**Request:**
```bash
curl http://localhost:5000/
```
**Response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "DESKTOP-ACLPNEC",
    "platform": "Windows",
    "platform_version": "Windows-11-10.0.26100-SP0",
    "architecture": "AMD64",
    "cpu_count": 12,
    "python_version": "3.13.7"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-25T18:00:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.9.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```
**Testing Commands:**
```bash
# Basic request
curl http://localhost:5000/

# Pretty-printed JSON (requires jq)
curl http://localhost:5000/ | jq

# With custom port
curl http://localhost:8080/
```

### Endpoint: `GET /health`

**Description**: Health check endpoint for monitoring and Kubernetes probes

**Request:**
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-25T18:00:00.000000+00:00",
  "uptime_seconds": 3600
}
```
**HTTP Status**: `200 OK` when healthy

**Testing Commands:**
```bash
# Basic health check
curl http://localhost:5000/health
# Pretty-printed JSON (requires jq)
curl http://localhost:5000/health | jq
```

## Challenges & Solutions

### Challenge 1: Understanding FastAPI vs Flask
**Problem:** Coming from minimal Python experience, understanding the differences between FastAPI and Flask, and how to properly structure FastAPI applications.

**Solution:**
- Studied FastAPI documentation and examples
- Understood that FastAPI uses async/await patterns
- Learned that FastAPI automatically handles JSON serialization
- Realized that FastAPI's type hints enable automatic validation

### Challenge 2: PEP 8 Compliance
**Problem**: Ensuring code follows PEP 8 style guidelines

**Solution:**
- Installed autopep8 tool
- Used autopep8 --in-place -a app.py to automatically fix style issues

## GitHub Community
**Why Starring Repositories Matters**
Starring repositories serves multiple purposes in open source development. First, it acts as a bookmarking mechanism, allowing developers to save interesting projects for future reference. More importantly, stars signal community appreciation and project quality—high star counts indicate that a project is trusted and valuable, which helps other developers discover useful tools. Stars also encourage maintainers by showing that their work is valued, and they help projects gain visibility in GitHub's search and recommendation algorithms. For students and professionals, a curated list of starred repositories demonstrates awareness of industry best practices and quality tools

**How Following Developers Helps**
Following developers on GitHub is valuable for both team collaboration and professional growth. In team projects, following classmates allows you to stay updated on their work, discover new approaches to problems, and build a supportive learning community. It makes it easier to find potential collaborators for future projects and creates opportunities for knowledge sharing. From a professional development perspective, following experienced developers and thought leaders exposes you to high-quality code, innovative solutions, and industry trends in real-time. You can learn from their commit patterns, project structures, and problem-solving approaches, which accelerates your own growth as a developer. This networking also helps build your professional presence in the developer community, as your GitHub activity shows employers your interests, engagement, and commitment to continuous learning