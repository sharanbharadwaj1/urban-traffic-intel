from app.core.config import Settings
from app.repositories.events import EventRepository
from app.repositories.jobs import JobRepository
from app.services.alerts import AlertService
from app.services.frame_pipeline import FramePipeline
from app.services.graph import GraphService
from app.services.inference import InferenceService
from app.services.jobs import JobService
from app.services.plates import PlateService
from app.services.storage import StorageService
from app.services.video_ingestion import VideoIngestionService


class ServiceContainer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.storage_service = StorageService(settings)
        self.inference_service = InferenceService(settings)
        self.video_ingestion_service = VideoIngestionService(settings)
        self.frame_pipeline = FramePipeline(settings)
        self.alert_service = AlertService(settings)
        self.plate_service = PlateService(settings)
        self.graph_service = GraphService(settings)
        self.job_repository = JobRepository()
        self.event_repository = EventRepository()
        self.job_service = JobService(
            settings=settings,
            storage_service=self.storage_service,
            video_ingestion_service=self.video_ingestion_service,
            frame_pipeline=self.frame_pipeline,
            inference_service=self.inference_service,
            alert_service=self.alert_service,
            plate_service=self.plate_service,
            graph_service=self.graph_service,
            job_repository=self.job_repository,
            event_repository=self.event_repository,
        )
