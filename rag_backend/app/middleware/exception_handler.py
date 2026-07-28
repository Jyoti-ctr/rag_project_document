"""
middleware/exception_handler.py
---------------------------------
Custom ASGI middleware that catches any unhandled exception raised
while processing a request, logs it into the `error_logs` MongoDB
collection, and returns a clean, generic JSON 500 response to the client.
"""

import logging
import traceback
from datetime import datetime, timezone

from fastapi import Request, status
from fastapi.responses import JSONResponse
from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.database import get_error_logs_collection
from app.utils.security import decode_access_token

logger = logging.getLogger(__name__)


def _extract_user_id(request: Request) -> str | None:
    """Best-effort extraction of the user id from the Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return None

    token = auth_header.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
        return payload.get("sub")
    except JWTError:
        return None


class ExceptionLoggingMiddleware(BaseHTTPMiddleware):
    """
    Wraps every request. On unhandled exception:
      1. Logs full traceback to stdout.
      2. Persists a structured error record into MongoDB.
      3. Returns a generic {"detail": "Internal Server Error"} 500 response.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        try:
            return await call_next(request)
        except Exception as exc:  # noqa: BLE001 - intentionally broad; this is the safety net
            logger.exception("Unhandled exception while processing request")

            user_id = _extract_user_id(request)
            error_record = {
                "timestamp": datetime.now(timezone.utc),
                "endpoint": request.url.path,
                "method": request.method,
                "error_message": str(exc),
                "stack_trace": traceback.format_exc(),
                "user_id": user_id,
            }

            try:
                error_logs_collection = get_error_logs_collection()
                await error_logs_collection.insert_one(error_record)
            except Exception:
                # If logging itself fails (e.g. DB down), don't crash the response cycle.
                logger.exception("Failed to persist error log to MongoDB")

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal Server Error"},
            )
