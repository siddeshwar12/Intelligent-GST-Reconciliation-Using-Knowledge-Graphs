"""Custom middleware for FastAPI application."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)


async def log_requests_middleware(request: Request, call_next):
    """
    Middleware to log all requests and responses.
    
    Args:
        request: FastAPI request
        call_next: Next middleware/endpoint
        
    Returns:
        Response
    """
    # Log request
    start_time = time.time()
    request_id = str(time.time())
    
    logger.info(
        f"Request started: {request.method} {request.url.path} "
        f"[ID: {request_id}]"
    )
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"[ID: {request_id}] [Status: {response.status_code}] "
            f"[Time: {process_time:.3f}s]"
        )
        
        return response
        
    except Exception as e:
        # Log error
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"[ID: {request_id}] [Error: {str(e)}] "
            f"[Time: {process_time:.3f}s]"
        )
        raise


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with custom response format.
    
    Args:
        request: FastAPI request
        exc: Validation exception
        
    Returns:
        JSON response with error details
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": errors,
            "timestamp": datetime.now().isoformat()
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions with custom response format.
    
    Args:
        request: FastAPI request
        exc: HTTP exception
        
    Returns:
        JSON response with error details
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail,
            "details": None,
            "timestamp": datetime.now().isoformat()
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle general exceptions with custom response format.
    
    Args:
        request: FastAPI request
        exc: Exception
        
    Returns:
        JSON response with error details
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An internal server error occurred",
            "details": {"exception": str(exc)},
            "timestamp": datetime.now().isoformat()
        }
    )


class SecurityHeadersMiddleware:
    """Middleware to add security headers to responses."""
    
    def __init__(self, app):
        """Initialize middleware."""
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """Process request and add security headers."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                
                # Add security headers
                headers[b"X-Content-Type-Options"] = b"nosniff"
                headers[b"X-Frame-Options"] = b"DENY"
                headers[b"X-XSS-Protection"] = b"1; mode=block"
                headers[b"Strict-Transport-Security"] = b"max-age=31536000; includeSubDomains"
                
                message["headers"] = list(headers.items())
            
            await send(message)
        
        await self.app(scope, receive, send_with_headers)


class RateLimitMiddleware:
    """Middleware for rate limiting (placeholder implementation)."""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            calls: Number of calls allowed
            period: Time period in seconds
        """
        self.app = app
        self.calls = calls
        self.period = period
        self.requests = {}
    
    async def __call__(self, scope, receive, send):
        """Process request with rate limiting."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # TODO: Implement actual rate limiting logic
        # For now, just pass through
        await self.app(scope, receive, send)
