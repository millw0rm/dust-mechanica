import json
import logging
import threading
from fastapi import FastAPI, Request
from apps.api.deps import get_trace_id
from apps.api.routes.health import router as health_router
from apps.api.routes.requirements import router as req_router
from apps.api.routes.candidates import router as cand_router, repo
from apps.worker.runner import worker_loop

app = FastAPI(title="Dust Mechanica API")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dust.api")


@app.on_event("startup")
def startup_worker():
    threading.Thread(target=worker_loop, args=(repo,), daemon=True).start()


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
