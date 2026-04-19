from datetime import datetime

from pydantic import BaseModel


class UploadVideoResponse(BaseModel):
    job_id: str
    queue_task_id: str | None
    status: str
    source_type: str
    message: str
    events_url: str


class JobResponse(BaseModel):
    job_id: str
    queue_task_id: str | None
    camera_id: str
    source_type: str
    source_uri: str
    storage_key: str | None
    status: str
    error_message: str | None
    total_frames: int
    processed_frames: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class JobListResponse(BaseModel):
    items: list[JobResponse]
    count: int


class LiveStateResponse(BaseModel):
    job_id: str
    camera_id: str
    frame_index: int
    updated_at: str
    image_url: str
    alerts: list[dict]
    tracked_objects: list[dict]


class EventResponse(BaseModel):
    id: int
    job_id: str
    camera_id: str
    event_type: str
    event_timestamp: datetime
    frame_index: int
    track_id: int | None
    plate: str | None
    class_name: str | None
    confidence: float | None
    bbox: dict | None
    metadata: dict


class EventListResponse(BaseModel):
    items: list[EventResponse]
    count: int


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    storage_backend: str
    database: str
    plate_detection_enabled: bool
    graph_enabled: bool
    broker_url: str
