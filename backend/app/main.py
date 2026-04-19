from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine
from app.services.dependencies import ServiceContainer


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    Base.metadata.create_all(bind=engine)
    app.state.container = ServiceContainer(settings=settings)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
    )
    application.include_router(router)
    application.mount("/assets", StaticFiles(directory=settings.local_storage_path), name="assets")
    return application


app = create_app()
