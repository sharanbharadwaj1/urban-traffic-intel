import logging
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import cv2
from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings
from app.db.models import EventRecord, ProcessingJob
from app.db.session import SessionLocal
from app.kafka_queue import KafkaJobQueue
from app.repositories.events import EventRepository
from app.repositories.jobs import JobRepository
from app.schemas.api import EventListResponse, EventResponse, JobListResponse, JobResponse, LiveStateResponse
from app.services.alerts import AlertService
from app.services.frame_pipeline import FramePipeline
from app.services.graph import GraphService
from app.services.inference import InferenceService
from app.services.plates import PlateService
from app.services.storage import StorageService
from app.services.tracking import SimpleTracker
from app.services.video_ingestion import VideoIngestionService


logger = logging.getLogger(__name__)


class JobService:
    def __init__(
        self,
        settings: Settings,
        storage_service: StorageService,
        video_ingestion_service: VideoIngestionService,
        frame_pipeline: FramePipeline,
        inference_service: InferenceService,
        alert_service: AlertService,
        plate_service: PlateService,
        graph_service: GraphService,
        job_repository: JobRepository,
        event_repository: EventRepository,
    ) -> None:
        self.settings = settings
        self.storage_service = storage_service
        self.video_ingestion_service = video_ingestion_service
        self.frame_pipeline = frame_pipeline
        self.inference_service = inference_service
        self.alert_service = alert_service
        self.plate_service = plate_service
        self.graph_service = graph_service
        self.job_repository = job_repository
        self.event_repository = event_repository

    async def create_file_job(self, file: UploadFile, camera_id: str) -> ProcessingJob:
        suffix = Path(file.filename or "upload.mp4").suffix or ".mp4"
        job_id = uuid.uuid4().hex
        local_path = self.settings.upload_temp_path / f"{job_id}{suffix}"
        with local_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        await file.close()

        job = self._create_job(
            job_id=job_id,
            camera_id=camera_id,
            source_type="file",
            source_uri=str(local_path),
        )
        return self.enqueue_job(job.job_id)

    async def create_rtsp_job(self, rtsp_url: str, camera_id: str) -> ProcessingJob:
        job_id = uuid.uuid4().hex
        job = self._create_job(
            job_id=job_id,
            camera_id=camera_id,
            source_type="rtsp",
            source_uri=rtsp_url,
        )
        return self.enqueue_job(job.job_id)

    def list_events(self, job_id: str | None, limit: int, event_type: str | None) -> EventListResponse:
        with SessionLocal() as db:
            events = self.event_repository.list(db=db, job_id=job_id, limit=limit, event_type=event_type)

        items = [
            EventResponse(
                id=event.id,
                job_id=event.job_id,
                camera_id=event.camera_id,
                event_type=event.event_type,
                event_timestamp=event.event_timestamp,
                frame_index=event.frame_index,
                track_id=event.track_id,
                plate=event.plate,
                class_name=event.class_name,
                confidence=event.confidence,
                bbox=event.bbox,
                metadata=event.metadata_json,
            )
            for event in events
        ]
        return EventListResponse(items=items, count=len(items))

    def get_job(self, job_id: str) -> JobResponse:
        with SessionLocal() as db:
            job = self.job_repository.get(db=db, job_id=job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
        return self._serialize_job(job)

    def list_jobs(self, limit: int) -> JobListResponse:
        with SessionLocal() as db:
            jobs = self.job_repository.list(db=db, limit=limit)
        items = [self._serialize_job(job) for job in jobs]
        return JobListResponse(items=items, count=len(items))

    def get_live_state(self, job_id: str) -> LiveStateResponse:
        state_path = self.storage_service.local_path_for_key(f"live/{job_id}/state.json")
        if not state_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Live state not available yet.")
        import json
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        return LiveStateResponse(**payload)

    def _create_job(self, job_id: str, camera_id: str, source_type: str, source_uri: str) -> ProcessingJob:
        job = ProcessingJob(
            job_id=job_id,
            camera_id=camera_id,
            source_type=source_type,
            source_uri=source_uri,
            status="queued",
        )
        with SessionLocal() as db:
            return self.job_repository.create(db=db, job=job)

    def enqueue_job(self, job_id: str) -> ProcessingJob:
        try:
            queue_task_id = KafkaJobQueue(
                bootstrap_servers=self.settings.kafka_bootstrap_servers,
                topic=self.settings.kafka_job_topic,
            ).enqueue(job_id)
        except Exception as exc:
            logger.exception("job_enqueue_failed", extra={"job_id": job_id})
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to enqueue job: {exc}",
            ) from exc
        with SessionLocal() as db:
            self.job_repository.attach_task(db=db, job_id=job_id, queue_task_id=queue_task_id)
            job = self.job_repository.get(db=db, job_id=job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found after enqueue.")
        return job

    def process_job(self, job_id: str) -> None:
        with SessionLocal() as db:
            job = self.job_repository.get(db=db, job_id=job_id)
            if job is None:
                return
            self.job_repository.mark_running(db=db, job_id=job_id)

        tracker = SimpleTracker(max_distance=self.settings.tracker_max_distance)
        alert_service = AlertService(self.settings)
        plate_service = PlateService(self.settings)
        processed_frames = 0
        total_frames = 0
        capture = None

        try:
            with SessionLocal() as db:
                job = self.job_repository.get(db=db, job_id=job_id)
                if job is None:
                    return

                if job.source_type == "file":
                    storage_key = self.storage_service.store_file(job_id=job.job_id, source_path=Path(job.source_uri))
                    self.job_repository.attach_storage_key(db=db, job_id=job.job_id, storage_key=storage_key)

            capture, estimated_frames = self.video_ingestion_service.open_source(job_id=job_id)
            total_frames = estimated_frames

            event_rows: list[EventRecord] = []
            for frame_index, frame in self.video_ingestion_service.read_frames(capture):
                total_frames = max(total_frames, frame_index)
                if not self.frame_pipeline.should_process(frame_index):
                    continue

                packet = self.frame_pipeline.preprocess(frame_index=frame_index, frame=frame)
                detections, inference_time_ms = self.inference_service.infer(packet.frame)
                tracked_objects = tracker.update(detections)
                track_plates: dict[int, str] = {}
                for tracked_object in tracked_objects:
                    confirmed_plate = plate_service.process_track(
                        tracked_object=tracked_object,
                        frame_index=packet.frame_index,
                        frame=packet.frame,
                    )
                    if confirmed_plate:
                        track_plates[tracked_object.track_id] = confirmed_plate
                        with SessionLocal() as plate_db:
                            self.event_repository.update_plate_for_track(
                                db=plate_db,
                                job_id=job_id,
                                camera_id=job.camera_id,
                                track_id=tracked_object.track_id,
                                plate=confirmed_plate,
                            )
                        self.graph_service.write_vehicle_sighting(
                            plate=confirmed_plate,
                            camera_id=job.camera_id,
                            track_id=tracked_object.track_id,
                            frame_id=packet.frame_index,
                            class_name=tracked_object.class_name,
                            confidence=tracked_object.confidence,
                        )
                events = alert_service.evaluate(
                    frame_index=packet.frame_index,
                    timestamp=packet.timestamp,
                    tracked_objects=tracked_objects,
                )

                for event in events:
                    snapshot_url = self._store_event_snapshot(
                        job_id=job_id,
                        frame_index=event.frame_index,
                        event_type=event.event_type,
                        frame=packet.frame,
                        bbox=event.bbox,
                    )
                    event_rows.append(
                        EventRecord(
                            job_id=job_id,
                            camera_id=job.camera_id,
                            event_type=event.event_type,
                            event_timestamp=event.timestamp,
                            frame_index=event.frame_index,
                            track_id=event.track_id,
                            plate=track_plates.get(event.track_id) or plate_service.get_plate(event.track_id) if event.track_id is not None else None,
                            class_name=event.class_name,
                            confidence=event.confidence,
                            bbox=event.bbox,
                            metadata_json={
                                **event.metadata,
                                "inference_time_ms": inference_time_ms,
                                "detections_in_frame": len(detections),
                                "snapshot_url": snapshot_url,
                            },
                        )
                    )

                if event_rows:
                    with SessionLocal() as event_db:
                        self.event_repository.add_many(db=event_db, rows=event_rows)
                    event_rows = []

                self._store_live_preview(
                    job_id=job_id,
                    camera_id=job.camera_id,
                    frame_index=packet.frame_index,
                    frame=packet.frame,
                    tracked_objects=tracked_objects,
                    plate_service=plate_service,
                    events=events,
                )

                processed_frames += 1
                if processed_frames % 10 == 0:
                    with SessionLocal() as progress_db:
                        self.job_repository.update_progress(
                            db=progress_db,
                            job_id=job_id,
                            processed_frames=processed_frames,
                            total_frames=total_frames,
                        )

            with SessionLocal() as completed_db:
                self.job_repository.mark_completed(
                    db=completed_db,
                    job_id=job_id,
                    processed_frames=processed_frames,
                    total_frames=total_frames,
                )
        except Exception as exc:
            logger.exception("job_failed", extra={"job_id": job_id})
            with SessionLocal() as failed_db:
                self.job_repository.mark_failed(db=failed_db, job_id=job_id, error_message=str(exc))
        finally:
            self.video_ingestion_service.close(capture)

    @staticmethod
    def _serialize_job(job: ProcessingJob) -> JobResponse:
        return JobResponse(
            job_id=job.job_id,
            queue_task_id=job.queue_task_id,
            camera_id=job.camera_id,
            source_type=job.source_type,
            source_uri=job.source_uri,
            storage_key=job.storage_key,
            status=job.status,
            error_message=job.error_message,
            total_frames=job.total_frames,
            processed_frames=job.processed_frames,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )

    def _store_event_snapshot(
        self,
        job_id: str,
        frame_index: int,
        event_type: str,
        frame,
        bbox: dict | None,
    ) -> str | None:
        if not self.settings.save_event_snapshots:
            return None

        snapshot = frame.copy()
        if bbox:
            x1 = int(bbox.get("x1", 0))
            y1 = int(bbox.get("y1", 0))
            x2 = int(bbox.get("x2", 0))
            y2 = int(bbox.get("y2", 0))
            cv2.rectangle(snapshot, (x1, y1), (x2, y2), (18, 92, 235), 2)
            cv2.putText(
                snapshot,
                event_type,
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (18, 92, 235),
                2,
                cv2.LINE_AA,
            )

        ok, encoded = cv2.imencode(".jpg", snapshot)
        if not ok:
            return None

        key = f"snapshots/{job_id}/{frame_index}-{event_type}-{uuid.uuid4().hex[:8]}.jpg"
        stored_path = self.storage_service.store_bytes(key=key, payload=encoded.tobytes(), content_type="image/jpeg")
        if stored_path.startswith("s3://"):
            return stored_path
        return f"/assets/{key}"

    def _store_live_preview(
        self,
        job_id: str,
        camera_id: str,
        frame_index: int,
        frame,
        tracked_objects: list,
        plate_service: PlateService,
        events: list,
    ) -> None:
        annotated = frame.copy()
        alert_track_ids = {event.track_id for event in events if event.track_id is not None}
        for tracked in tracked_objects:
            x1, y1, x2, y2 = map(int, tracked.bbox)
            is_alert = tracked.track_id in alert_track_ids
            color = (0, 64, 255) if is_alert else (0, 255, 0)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            plate = plate_service.get_plate(tracked.track_id)
            label_parts = [f"ID {tracked.track_id}", tracked.class_name]
            if plate:
                label_parts.append(plate)
            label = " | ".join(label_parts)
            cv2.putText(
                annotated,
                label,
                (x1, max(24, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
                cv2.LINE_AA,
            )

        alert_names = [event.event_type for event in events]
        if alert_names:
            cv2.putText(
                annotated,
                "ALERT: " + ", ".join(alert_names[:3]),
                (18, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 64, 255),
                2,
                cv2.LINE_AA,
            )

        ok, encoded = cv2.imencode(".jpg", annotated)
        if not ok:
            return

        image_key = f"live/{job_id}/latest.jpg"
        self.storage_service.store_bytes(image_key, encoded.tobytes(), content_type="image/jpeg")
        state_key = f"live/{job_id}/state.json"
        payload = {
            "job_id": job_id,
            "camera_id": camera_id,
            "frame_index": frame_index,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "image_url": f"/assets/{image_key}",
            "alerts": [
                {
                    "event_type": event.event_type,
                    "track_id": event.track_id,
                    "plate": plate_service.get_plate(event.track_id) if event.track_id is not None else None,
                }
                for event in events
            ],
            "tracked_objects": [
                {
                    "track_id": tracked.track_id,
                    "class_name": tracked.class_name,
                    "confidence": tracked.confidence,
                    "bbox": tracked.bbox_dict,
                    "plate": plate_service.get_plate(tracked.track_id),
                }
                for tracked in tracked_objects
            ],
        }
        self.storage_service.store_json(state_key, payload)
