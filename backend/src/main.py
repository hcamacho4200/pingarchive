"""Main module"""

import logging
import os
from typing import Any, cast

import typer
import uvicorn

from db import Database
from environment import get_settings
from logging_setup import reset_logging, setup_logging

logger: logging.Logger = logging.getLogger(__name__)

app = typer.Typer(help="PingArchive Backend")


@app.callback()
def startup_callback():
    """Startup function for the app called my typer callback"""
    print("here")
    env_vars = dict(os.environ)
    if not env_vars.get("PYTEST_VERSION"):
        run_migrations()
    app_init()


def app_init():
    """app initialization to setup logging"""
    global logger  # pylint: disable=global-statement
    settings = get_settings()
    reset_logging()
    log_level: int = logging.INFO

    if settings.log_level == "DEBUG":
        log_level = logging.DEBUG
    elif settings.log_level == "ERROR":
        log_level = logging.ERROR
    elif settings.log_level == "WARNING":
        log_level = logging.WARNING
    elif settings.log_level == "INFO":
        log_level = logging.INFO
    elif settings.log_level == "CRITICAL":
        log_level = logging.CRITICAL

    setup_logging(level=log_level)
    logger = logging.getLogger(__name__)
    logger.info("Starting app...")
    _ = Database()


def run_migrations():
    """Execute Alembic Migrations"""
    from alembic import command  # pylint: disable=import-outside-toplevel
    from alembic.config import Config  # pylint: disable=import-outside-toplevel

    _ = Database()
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@app.command()
def version():
    """Prints the version of the application"""
    settings = get_settings()
    print(f"Options Collector Version: {settings.version}")

@app.command()
def execute_api():
    """Run FastAPI only."""
    settings = get_settings()
    startup = {
        "host": settings.api_host,
        "port": settings.api_port,
        "reload": settings.api_reload,
        "workers": settings.api_workers,
    }
    logger.info("Starting FastAPI with settings: %s", startup)
    uvicorn.run("api.app:app", **startup)


if __name__ == "__main__":
    app()
