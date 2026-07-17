from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine
from app.kafka_queue import consume_jobs
from app.services.dependencies import ServiceContainer


settings = get_settings()
configure_logging(settings.log_level)
Base.metadata.create_all(bind=engine)


def process_video_job(job_id: str) -> None:
    container = ServiceContainer(settings=settings)
    container.job_service.process_job(job_id=job_id)


def run_worker() -> None:
    for payload, consumer in consume_jobs(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        topic=settings.kafka_job_topic,
        group_id=settings.kafka_job_group_id,
    ):
        process_video_job(job_id=payload["job_id"])
        consumer.commit()


if __name__ == "__main__":
    run_worker()
