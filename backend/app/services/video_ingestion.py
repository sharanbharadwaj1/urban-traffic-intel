import cv2

from app.core.config import Settings
from app.db.session import SessionLocal
from app.repositories.jobs import JobRepository


class VideoIngestionService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.job_repository = JobRepository()

    def open_source(self, job_id: str):
        with SessionLocal() as db:
            job = self.job_repository.get(db=db, job_id=job_id)
            if job is None:
                raise ValueError(f"Job {job_id} not found.")
            source = job.source_uri

        capture = cv2.VideoCapture(source)
        if not capture.isOpened():
            raise RuntimeError(f"Unable to open video source: {source}")

        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        return capture, total_frames

    def read_frames(self, capture):
        frame_index = 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            frame_index += 1
            yield frame_index, frame

    def close(self, capture) -> None:
        if capture is not None:
            capture.release()
