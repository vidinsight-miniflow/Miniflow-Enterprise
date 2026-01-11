import functools
from typing import Optional

from .context import trace

def with_trace(
    correlation_id: Optional[str] = None,
    session_id: Optional[str] = None,
):
    def decorator(func):
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with trace(correlation_id=correlation_id, session_id=session_id):
                return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            async with trace(correlation_id=correlation_id, session_id=session_id):
                return await func(*args, **kwargs)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator