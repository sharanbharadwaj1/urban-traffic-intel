from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ProcessingJob


class JobRepository:
    def create(self, db: Session, job: ProcessingJob) -> ProcessingJob:
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def get(self, db: Session, job_id: str) -> ProcessingJob | None:
        stmt = select(ProcessingJob).where(ProcessingJob.job_id == job_id)
        return db.scalar(stmt)

    def list(self, db: Session, limit: int) -> list[ProcessingJob]:
        stmt = select(ProcessingJob).order_by(ProcessingJob.created_at.desc()).limit(limit)
        return list(db.scalars(stmt))

    def attach_task(self, db: Session, job_id: str, queue_task_id: str) -> None:
        job = self.get(db, job_id)
        if job is None:
            return
        job.queue_task_id = queue_task_id
        db.commit()

    def mark_running(self, db: Session, job_id: str) -> None:
        job = self.get(db, job_id)
        if job is None:
            return
        job.status = "running"
        job.error_message = None
        job.started_at = datetime.now(timezone.utc)
        db.commit()

    def update_progress(self, db: Session, job_id: str, processed_frames: int, total_frames: int | None = None) -> None:
        job = self.get(db, job_id)
        if job is None:
            return
        job.processed_frames = processed_frames
        if total_frames is not None:
            job.total_frames = total_frames
        db.commit()

    def attach_storage_key(self, db: Session, job_id: str, storage_key: str) -> None:
        job = self.get(db, job_id)
        if job is None:
            return
        job.storage_key = storage_key
        db.commit()

    def mark_completed(self, db: Session, job_id: str, processed_frames: int, total_frames: int) -> None:
        job = self.get(db, job_id)
        if job is None:
            return
        job.status = "completed"
        job.processed_frames = processed_frames
        job.total_frames = total_frames
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    def mark_failed(self, db: Session, job_id: str, error_message: str) -> None:
        job = self.get(db, job_id)
        if job is None:
            return
        job.status = "failed"
        job.error_message = error_message
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
