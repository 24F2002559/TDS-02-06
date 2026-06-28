import time
import uuid
from collections import deque
from fastapi import FastAPI, Query, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from prometheus_client import Counter, generate_latest, REGISTRY

app = FastAPI()

# ----- Prometheus counter -----
http_counter = Counter('http_requests_total', 'Total HTTP requests', ['method', 'path'])

# ----- Log storage (last 1000 entries) -----
log_entries = deque(maxlen=1000)

# ----- Start time -----
start_time = time.time()

@app.middleware("http")
async def observe_and_log(request: Request, call_next):
    # Count this request
    http_counter.labels(method=request.method, path=request.url.path).inc()
    req_id = str(uuid.uuid4())[:8]

    response = await call_next(request)

    # Save log entry
    log_entries.append({
        "level": "INFO",
        "ts": time.time(),
        "path": request.url.path,
        "request_id": req_id
    })
    response.headers["X-Request-ID"] = req_id
    return response

@app.get("/work")
async def work(n: int = Query(..., description="Work units")):
    return {"email": "24f2002559@ds.study.iitm.ac.in", "done": n}   # <-- USE YOUR REAL EMAIL

@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(REGISTRY), media_type="text/plain")

@app.get("/healthz")
async def healthz():
    uptime = time.time() - start_time
    return {"status": "ok", "uptime_s": round(uptime, 2)}

@app.get("/logs/tail")
async def logs_tail(limit: int = 10):
    recent = list(log_entries)[-limit:] if limit > 0 else []
    return JSONResponse(content=recent)
