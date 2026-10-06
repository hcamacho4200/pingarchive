"""FastAPI application"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.ping_destinations_router import router as ping_destinations_router
from api.routes.ping_measurements_router import router as ping_measurements_router
from environment import get_settings
from logging_setup import reset_logging, setup_logging

reset_logging()
setup_logging(log_name="ping_archive_api", log_dir="logs", level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="PingArchive API",
    version=settings.version,
)

API_V1_PREFIX = "/api/v1"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://192.168.1.121:5173"],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ping_destinations_router, prefix=API_V1_PREFIX)
app.include_router(ping_measurements_router, prefix=API_V1_PREFIX)

logger.info("Environment: %s, %s", settings.environment, settings.log_level)
