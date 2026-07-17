from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status

from app.schemas.api import EventListResponse, GraphSightingListResponse, HealthResponse, JobListResponse, JobResponse, LiveStateResponse, UploadVideoResponse
from app.services.dependencies import ServiceContainer
from app.ui import render_upload_dashboard

router = APIRouter()


def get_container(request: Request) -> ServiceContainer:
    return request.app.state.container


@router.get("/", tags=["ui"], include_in_schema=False)
def dashboard():
    return render_upload_dashboard()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health(container: ServiceContainer = Depends(get_container)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=container.inference_service.is_model_available,
        storage_backend=container.storage_service.backend_name,
        database="connected",
        plate_detection_enabled=container.plate_service.enabled,
        graph_enabled=container.graph_service.enabled,
        kafka_bootstrap_servers=container.settings.kafka_bootstrap_servers,
    )


@router.post(
    "/upload-video",
    response_model=UploadVideoResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["videos"],
)
async def upload_video(
    request: Request,
    file: UploadFile | None = File(default=None),
    rtsp_url: str | None = Form(default=None),
    camera_id: str = Form(default="default-camera"),
    container: ServiceContainer = Depends(get_container),
) -> UploadVideoResponse:
    if file is None and not rtsp_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either a video file upload or an RTSP URL.",
        )

    if file is not None and rtsp_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide only one source per request.",
        )

    if file is not None:
        job = await container.job_service.create_file_job(file=file, camera_id=camera_id)
    else:
        job = await container.job_service.create_rtsp_job(rtsp_url=rtsp_url or "", camera_id=camera_id)

    return UploadVideoResponse(
        job_id=job.job_id,
        queue_task_id=job.queue_task_id,
        status=job.status,
        source_type=job.source_type,
        message="Video accepted for asynchronous processing.",
        events_url=str(request.url_for("get_events")) + f"?job_id={job.job_id}",
    )


@router.get("/jobs/{job_id}", response_model=JobResponse, tags=["jobs"])
def get_job(
    job_id: str,
    container: ServiceContainer = Depends(get_container),
) -> JobResponse:
    return container.job_service.get_job(job_id=job_id)


@router.get("/jobs/{job_id}/live-state", response_model=LiveStateResponse, tags=["jobs"])
def get_live_state(
    job_id: str,
    container: ServiceContainer = Depends(get_container),
) -> LiveStateResponse:
    return container.job_service.get_live_state(job_id=job_id)


@router.get("/jobs", response_model=JobListResponse, tags=["jobs"])
def list_jobs(
    limit: int = Query(default=50, ge=1, le=500),
    container: ServiceContainer = Depends(get_container),
) -> JobListResponse:
    return container.job_service.list_jobs(limit=limit)


@router.get("/events", response_model=EventListResponse, tags=["events"], name="get_events")
def get_events(
    job_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    event_type: str | None = Query(default=None),
    container: ServiceContainer = Depends(get_container),
) -> EventListResponse:
    return container.job_service.list_events(job_id=job_id, limit=limit, event_type=event_type)


@router.get("/graph/sightings", response_model=GraphSightingListResponse, tags=["graph"])
def get_graph_sightings(
    camera_id: str = Query(...),
    limit: int = Query(default=10, ge=1, le=100),
    container: ServiceContainer = Depends(get_container),
) -> GraphSightingListResponse:
    items = container.graph_service.get_camera_sightings(camera_id=camera_id, limit=limit)
    return GraphSightingListResponse(items=items, count=len(items))
