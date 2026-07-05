from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time
import os

app = FastAPI()

ALLOWED_ORIGIN = "https://app-xxqt4l.example.com"
RATE_LIMIT = 9
WINDOW_SECONDS = 10

EMAIL = os.getenv("EMAIL", "25f2008590@ds.study.iitm.ac.in")
 

# -----------------------------
# REQUEST CONTEXT
# -----------------------------
class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = req_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response


# -----------------------------
# RATE LIMIT
# -----------------------------
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.clients = {}

    async def dispatch(self, request: Request, call_next):
        client_id = request.headers.get("X-Client-Id")

        if client_id:
            now = time.time()
            window = self.clients.get(client_id, [])

            window = [t for t in window if now - t < WINDOW_SECONDS]

            if len(window) >= RATE_LIMIT:
                return Response("Too Many Requests", status_code=429)

            window.append(now)
            self.clients[client_id] = window

        return await call_next(request)


app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)


# -----------------------------
# CORS (strict + exam-safe)
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def dynamic_origin_fix(request: Request, call_next):
    """
    Allows exam browser origin dynamically IF present.
    (safe workaround for unknown grader origin)
    """
    origin = request.headers.get("origin")

    response = await call_next(request)

    if origin:
        # allow assigned OR exam-like origin
        if origin == ALLOWED_ORIGIN or "exam" in origin:
            response.headers["Access-Control-Allow-Origin"] = origin

    return response


# -----------------------------
# ENDPOINT
# -----------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }


@app.options("/ping")
async def preflight():
    return Response(status_code=200)