from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import EventRecord


class EventRepository:
    def add_many(self, db: Session, rows: list[EventRecord]) -> None:
        if not rows:
            return
        db.add_all(rows)
        db.commit()

    def list(self, db: Session, job_id: str | None, limit: int, event_type: str | None) -> list[EventRecord]:
        stmt = select(EventRecord).order_by(desc(EventRecord.created_at)).limit(limit)
        if job_id:
            stmt = stmt.where(EventRecord.job_id == job_id)
        if event_type:
            stmt = stmt.where(EventRecord.event_type == event_type)
        return list(db.scalars(stmt))

    def update_plate_for_track(self, db: Session, job_id: str, camera_id: str, track_id: int, plate: str) -> None:
        rows = list(
            db.scalars(
                select(EventRecord).where(
                    EventRecord.job_id == job_id,
                    EventRecord.camera_id == camera_id,
                    EventRecord.track_id == track_id,
                    EventRecord.plate.is_(None),
                )
            )
        )
        for row in rows:
            row.plate = plate
            metadata = dict(row.metadata_json or {})
            metadata["plate"] = plate
            row.metadata_json = metadata
        db.commit()
