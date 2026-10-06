from fastapi import FastAPI, Request
from routes import auth, customer, analytics, prediction, assistant
from fastapi.middleware.cors import CORSMiddleware
import time
app = FastAPI()

from logging_config import setup_logger

logger = setup_logger("app", "app.log")

@app.middleware("http")
async def log_requests(request: Request, call_next):

    start_time = time.perf_counter()

    try:
        response = await call_next(request)

        duration = time.perf_counter() - start_time

        logger.info(
            "%s %s | status=%s | duration=%.3fs",
            request.method,
            request.url.path,
            response.status_code,
            duration
        )

        return response

    except Exception:
        duration = time.perf_counter() - start_time

        logger.exception(
            "%s %s | status=500 | duration=%.3fs",
            request.method,
            request.url.path,
            duration
        )

        raise


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(customer.router)
app.include_router(analytics.router)
app.include_router(prediction.router)
app.include_router(assistant.router)



