from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from uuid import uuid4
import time

app = FastAPI()

EMAIL = "25f2008590@ds.study.iitm.ac.in"

# ----------------------------
# CORS
# ----------------------------

allowed_origins = [
    "https://app-xxqt4l.example.com",
    "https://exam.sanand.workers.dev"
    # IMPORTANT
    # Add IITM exam origin below when they mention it.
    # Example:
    # "https://exam.sanand.workers.dev"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"], 
)

# ----------------------------
# Request Context Middleware
# ----------------------------

@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response

# ----------------------------
# Rate Limiter
# ----------------------------

RATE_LIMIT = 9
WINDOW = 10

clients = {}


class RateLimitMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        client = request.headers.get("X-Client-Id", "anonymous")

        now = time.time()

        history = clients.get(client, [])

        history = [t for t in history if now - t < WINDOW]

        if len(history) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )

        history.append(now)

        clients[client] = history

        return await call_next(request)


app.add_middleware(RateLimitMiddleware)

# ----------------------------
# Endpoint
# ----------------------------

@app.get("/ping")
async def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
