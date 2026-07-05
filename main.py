from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import time

app = FastAPI()

ALLOWED_ORIGINS = [
    "https://app-xxqt4l.example.com",
    "https://exam.sanand.workers.dev"
]

EMAIL = "25f2008590@ds.study.iitm.ac.in"
WINDOW_SECONDS = 10
MAX_REQUESTS = 9

clients = {}

@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    history = clients.get(client_id, [])
    history = [t for t in history if now - t < WINDOW_SECONDS]

    if len(history) >= MAX_REQUESTS:
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})

    history.append(now)
    clients[client_id] = history
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"], 
)

@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
