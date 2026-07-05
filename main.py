from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid

app = FastAPI()

EMAIL = "25f2008590@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://app-xxqt4l.example.com"

RATE_LIMIT = 9
WINDOW_SECONDS = 10


# -----------------------------
# Request Context Middleware
# -----------------------------
class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID")

        if not request_id:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)

        # Always echo request ID
        response.headers["X-Request-ID"] = request_id

        return response


# -----------------------------
# Rate Limit Middleware
# -----------------------------
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.clients = {}

    async def dispatch(self, request: Request, call_next):
        client_id = request.headers.get("X-Client-Id")

        if client_id:
            now = time.time()

            history = self.clients.get(client_id, [])
            history = [t for t in history if now - t < WINDOW_SECONDS]

            if len(history) >= RATE_LIMIT:
                response = Response(
                    content="Too Many Requests",
                    status_code=429,
                )

                # Echo request id even on 429
                request_id = request.headers.get("X-Request-ID")
                if not request_id:
                    request_id = str(uuid.uuid4())

                response.headers["X-Request-ID"] = request_id
                return response

            history.append(now)
            self.clients[client_id] = history

        return await call_next(request)


# -----------------------------
# CORS Middleware
# -----------------------------
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("Origin")

        response = await call_next(request)

        if origin == ALLOWED_ORIGIN:
            response.headers["Access-Control-Allow-Origin"] = origin

        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = (
            "X-Request-ID, X-Client-Id, Content-Type"
        )

        return response


# Middleware order
# Last added executes first.
app.add_middleware(CustomCORSMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }


@app.options("/ping")
async def ping_options():
    return Response(status_code=200)