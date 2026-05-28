from fastapi import Depends, FastAPI, Request
from apps.api.deps import get_trace_id
from apps.api.routes.health import router as health_router
from apps.api.routes.requirements import router as req_router
from apps.api.routes.candidates import router as cand_router

app = FastAPI(title="Dust Mechanica API")


@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    trace_id = request.headers.get("x-trace-id", "") or get_trace_id()
    response = await call_next(request)
    response.headers["x-trace-id"] = trace_id
    return response


app.include_router(health_router)
app.include_router(req_router)
app.include_router(cand_router)
