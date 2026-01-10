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
        
        # 7. CORS header'larını ekle (eğer yoksa)
        # Bu, CORS middleware'in çalışmadığı durumlar için fallback
        origin = request.headers.get("Origin")
        if origin and "Access-Control-Allow-Origin" not in response.headers:
            from miniflow.utils.handlers.configuration_handler import ConfigurationHandler
            try:
                ConfigurationHandler.ensure_loaded()
                allowed_origins = ConfigurationHandler.get_list("Server", "allowed_origins", "*")
                
                origin_allowed = False
                if isinstance(allowed_origins, list):
                    if "*" in allowed_origins or (len(allowed_origins) == 1 and allowed_origins[0] == "*"):
                        origin_allowed = True
                    elif origin in allowed_origins:
                        origin_allowed = True
                elif isinstance(allowed_origins, str):
                    if allowed_origins == "*" or origin == allowed_origins:
                        origin_allowed = True
                else:
                    origin_allowed = True
                
                if origin_allowed:
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD"
                    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-API-KEY, X-Request-ID, X-Correlation-ID, Accept, Origin, X-Requested-With"
                    response.headers["Access-Control-Expose-Headers"] = "X-Request-ID, X-Response-Time, X-Correlation-ID"
                    response.headers["Vary"] = "Origin"
            except Exception:
                pass
        
        return response