from celery import Celery

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine
from app.services.dependencies import ServiceContainer

settings = get_settings()
configure_logging(settings.log_level)
Base.metadata.create_all(bind=engine)

celery_app = Celery(
    "traffic_video_analytics",
    broker=settings.broker_url,
    backend=settings.result_backend_url,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_time_limit=60 * 60 * 4,
    worker_prefetch_multiplier=1,
)


@celery_app.task(name="app.worker.process_video_job")
def process_video_job(job_id: str) -> None:
    container = ServiceContainer(settings=settings)
    container.job_service.process_job(job_id=job_id)
