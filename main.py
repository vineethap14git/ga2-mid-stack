import time
import uuid
from collections import defaultdict, deque
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# -----------------------------
# CONFIG
# -----------------------------
ALLOWED_ORIGINS = [
    "https://app-xxqt4l.example.com",
    "https://exam-page.example.com"  # replace with actual exam origin if given
]

RATE_LIMIT = 9        # B requests
WINDOW = 10           # seconds

EMAIL = os.getenv("EMAIL", "user@example.com")

# -----------------------------
# RATE LIMIT STORAGE
# -----------------------------
client_hits = defaultdict(deque)

# -----------------------------
# MIDDLEWARE 1: REQUEST CONTEXT
# -----------------------------
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID")

    if not req_id:
        req_id = str(uuid.uuid4())

    request.state.request_id = req_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = req_id
    return response


# -----------------------------
# MIDDLEWARE 2: CORS (strict origin)
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# MIDDLEWARE 3: RATE LIMITER
# -----------------------------
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id")

    if not client_id:
        raise HTTPException(status_code=400, detail="Missing X-Client-Id")

    now = time.time()
    window_start = now - WINDOW

    q = client_hits[client_id]

    # remove old requests outside window
    while q and q[0] < window_start:
        q.popleft()

    if len(q) >= RATE_LIMIT:
        return Response(content="Too Many Requests", status_code=429)

    q.append(now)

    return await call_next(request)


# -----------------------------
# ROUTE
# -----------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }


# -----------------------------
# OPTIONS support (CORS preflight)
# -----------------------------
@app.options("/ping")
async def ping_options():
    return Response(status_code=200)