import logging
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.config import Settings, get_settings
from app.db import COLLECTION_NAME, ensure_indexes
from app.routers import analytics, cotizaciones

logger = logging.getLogger("hostech_api")


def create_app(
    settings: Settings | None = None,
    *,
    mongo_client_factory: Callable[..., Any] = MongoClient,
) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        mongo_uri, database_name = app_settings.mongo_configuration()
        client = mongo_client_factory(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            appname="HostechQuotesAPI",
        )
        try:
            database = client[database_name]
            database.command("ping")
            collection = database[COLLECTION_NAME]
            ensure_indexes(collection)
        except PyMongoError as exc:
            client.close()
            logger.error("MongoDB startup failed (%s).", type(exc).__name__)
            raise RuntimeError(
                "No se pudo inicializar la conexión con MongoDB."
            ) from None

        app.state.mongo_client = client
        app.state.quotes_collection = collection
        try:
            yield
        finally:
            client.close()

    app = FastAPI(
        title="Hostech Quotes API",
        description=(
            "CRUD y análisis de cotizaciones de hoteles con datos simulados."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.settings = app_settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )
    app.include_router(cotizaciones.router)
    app.include_router(analytics.router)

    @app.get("/health", tags=["sistema"], summary="Verificar API y MongoDB")
    def health(request: Request) -> JSONResponse:
        try:
            request.app.state.quotes_collection.database.command("ping")
        except PyMongoError as exc:
            logger.error("MongoDB health check failed (%s).", type(exc).__name__)
            return JSONResponse(
                status_code=503,
                content={"status": "unavailable", "database": "disconnected"},
            )
        return JSONResponse(
            content={
                "status": "ok",
                "database": "connected",
                "collection": COLLECTION_NAME,
            }
        )

    @app.exception_handler(PyMongoError)
    async def mongo_error_handler(
        _request: Request,
        exc: PyMongoError,
    ) -> JSONResponse:
        logger.error(
            "MongoDB request failed (%s) for %s.",
            type(exc).__name__,
            _request.url.path,
        )
        return JSONResponse(
            status_code=503,
            content={"detail": "La base de datos no está disponible."},
        )

    return app


app = create_app()
