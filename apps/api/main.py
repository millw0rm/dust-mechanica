import asyncio
import json
import logging
import threading
import time
from collections import deque
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from apps.api.deps import get_trace_id
from apps.api.routes.health import router as health_router
from apps.api.routes.requirements import router as req_router
from apps.api.routes.candidates import router as cand_router, repo
from apps.worker.runner import worker_loop

app = FastAPI(title="Dust Mechanica API")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dust.api")
RATE_WINDOW_SECONDS = 60
RATE_LIMIT = 120
MAX_REQUEST_BYTES = 512_000
REQUEST_TIMEOUT_SECONDS = 20
_recent = deque()


@app.on_event("startup")
def startup_worker():
    threading.Thread(target=worker_loop, args=(repo,), daemon=True).start()


@app.middleware("http")
async def guardrails(request: Request, call_next):
    now = time.time()
    while _recent and _recent[0] < now - RATE_WINDOW_SECONDS:
        _recent.popleft()
    if len(_recent) >= RATE_LIMIT:
        return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
    _recent.append(now)
    content_len = int(request.headers.get("content-length", "0") or "0")
    if content_len > MAX_REQUEST_BYTES:
        return JSONResponse({"detail": "request too large"}, status_code=413)
    try:
        return await asyncio.wait_for(call_next(request), timeout=REQUEST_TIMEOUT_SECONDS)
    except TimeoutError:
        return JSONResponse({"detail": "request timeout"}, status_code=504)


@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    trace_id = request.headers.get("x-trace-id", "") or get_trace_id()
    request_id = request.headers.get("x-request-id", "")
    response = await call_next(request)
    logger.info(json.dumps({"event": "request", "path": request.url.path, "trace_id": trace_id, "request_id": request_id}))
    response.headers["x-trace-id"] = trace_id
    return response


app.include_router(health_router)
app.include_router(req_router)
app.include_router(cand_router)
