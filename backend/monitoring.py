from time import perf_counter
from uuid import uuid4

from fastapi import Request


def start_request_context(request: Request):
    request.state.request_id = uuid4().hex[:12]
    request.state.started_at = perf_counter()


def finish_request_context(request: Request) -> dict:
    started_at = getattr(request.state, "started_at", None)
    duration_ms = None
    if started_at is not None:
        duration_ms = round((perf_counter() - started_at) * 1000, 2)
    return {
        "request_id": getattr(request.state, "request_id", None),
        "duration_ms": duration_ms,
    }
