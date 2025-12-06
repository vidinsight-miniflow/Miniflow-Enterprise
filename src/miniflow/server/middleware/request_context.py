import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class RequestContextMiddleware(BaseHTTPMiddleware):
    # Header names (industry standard)
    REQUEST_ID_HEADER = "X-Request-ID"
    CORRELATION_ID_HEADER = "X-Correlation-ID"
    RESPONSE_TIME_HEADER = "X-Response-Time"

    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Extract or generate request ID
        request_id = (
            request.headers.get(self.REQUEST_ID_HEADER) or
            request.headers.get(self.CORRELATION_ID_HEADER) or
            str(uuid.uuid4())
        )
        
        # 2. Record start time (high precision)
        start_time = time.perf_counter()
        
        # 3. Set request state
        request.state.request_id = request_id
        request.state.start_time = start_time
        
        # 4. Process request
        response = await call_next(request)
        
        # 5. Calculate response time
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # 6. Enrich response headers
        response.headers[self.REQUEST_ID_HEADER] = request_id
        response.headers[self.RESPONSE_TIME_HEADER] = f"{elapsed_ms:.2f}ms"
        
        return response