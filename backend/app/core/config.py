from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Traffic Video Analytics Service"
    log_level: str = "INFO"

    database_url: str = "sqlite:///./data/video_analytics.db"
    broker_url: str = "redis://localhost:6379/0"
    result_backend_url: str = "redis://localhost:6379/1"

    storage_backend: str = "local"
    storage_bucket: str = "traffic-video-analytics"
    storage_region: str = "us-east-1"
    storage_endpoint_url: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    local_storage_path: Path = Path("./data/storage")
    upload_temp_path: Path = Path("./data/uploads")

    model_path: str = "yolov8n.pt"
    confidence_threshold: float = Field(default=0.35, ge=0.0, le=1.0)
    frame_skip: int = Field(default=5, ge=1)
    frame_resize_width: int = Field(default=960, ge=0)
    stationary_frame_window: int = Field(default=12, ge=2)
    stationary_pixel_threshold: float = Field(default=18.0, gt=0)
    tracker_max_distance: float = Field(default=80.0, gt=0)
    max_parallel_jobs: int = Field(default=2, ge=1)
    alert_classes: str = "car,bus,truck,motorcycle,person"
    class_filter: str = "car,bus,truck,motorcycle,person"
    save_event_snapshots: bool = True
    plate_enabled: bool = False
    plate_confirmation_reads: int = Field(default=1, ge=1)
    plate_min_length: int = Field(default=7, ge=1)
    plate_max_length: int = Field(default=11, ge=1)
    plate_track_buffer_size: int = Field(default=6, ge=1)
    plate_track_process_top_k: int = Field(default=1, ge=1)
    plate_track_max_attempts: int = Field(default=12, ge=1)
    plate_track_ttl_frames: int = Field(default=90, ge=1)
    plate_retry_cooldown_frames: int = Field(default=20, ge=0)
    anpr_api_url: str = "https://api.platerecognizer.com/v1/plate-reader/"
    anpr_api_token: str | None = None
    anpr_country: str = "in"
    anpr_min_score: float = Field(default=0.5, ge=0.0)
    anpr_timeout_seconds: int = Field(default=15, ge=1)
    anpr_min_interval_seconds: float = Field(default=2.0, ge=0.0)
    anpr_retry_backoff_seconds: float = Field(default=5.0, ge=0.0)
    graph_enabled: bool = False
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    @property
    def alert_class_set(self) -> set[str]:
        return {item.strip() for item in self.alert_classes.split(",") if item.strip()}

    @property
    def class_filter_set(self) -> set[str]:
        return {item.strip() for item in self.class_filter.split(",") if item.strip()}


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.local_storage_path.mkdir(parents=True, exist_ok=True)
    settings.upload_temp_path.mkdir(parents=True, exist_ok=True)
    return settings
