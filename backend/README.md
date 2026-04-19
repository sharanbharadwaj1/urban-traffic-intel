# Production Video Analytics Backend

This folder contains a production-ready FastAPI backend that refactors the local surveillance pipeline into a single deployable service for AWS EC2. The legacy Redis-based services remain untouched in the repository; this backend is the new container-friendly runtime path.

## What Changed

- FastAPI API with:
  - `POST /upload-video`
  - `GET /events`
  - `GET /health`
- `GET /jobs`
  - `GET /jobs/{job_id}`
- queue-backed execution so uploads return immediately while workers process videos outside the API process
- modular pipeline split into:
  - video ingestion
  - frame extraction and preprocessing
  - model inference
  - plate detection and confirmation
  - alert generation
- optional Neo4j knowledge-graph persistence for confirmed vehicle sightings
- storage abstraction for local disk or S3-compatible object storage
- metadata persistence through a database abstraction layer backed by SQLAlchemy
- structured JSON logging for inference timing, detections, and failures

## Folder Layout

```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── repositories/
│   ├── schemas/
│   └── services/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Local Run

1. Create and activate a Python environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy the env template:

```powershell
Copy-Item .env.example .env
```

4. Start Redis:

```powershell
docker run -p 6379:6379 redis:7-alpine
```

5. Start the API:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

6. Start the worker:

```powershell
celery -A app.worker.celery_app worker --loglevel=info --pool=solo
```

Open [http://localhost:8000/docs](http://localhost:8000/docs).

## API Usage

### Upload a File

```bash
curl -X POST "http://localhost:8000/upload-video" \
  -F "file=@sample.mp4" \
  -F "camera_id=cam-01"
```

### Process an RTSP Stream

```bash
curl -X POST "http://localhost:8000/upload-video" \
  -F "rtsp_url=rtsp://user:pass@camera/stream" \
  -F "camera_id=cam-rtsp-01"
```

### Get Events

```bash
curl "http://localhost:8000/events?job_id=<job_id>"
```

### Get Job Status

```bash
curl "http://localhost:8000/jobs/<job_id>"
```

## Docker

Build and run:

```powershell
docker build -t traffic-video-analytics .
docker run -p 8000:8000 --env-file .env traffic-video-analytics
```

The container is CPU-optimized and exposes port `8000`.

## Docker Compose Stack

Run the full local stack:

```powershell
docker compose up --build
```

This starts:

- FastAPI API
- Celery worker
- Redis broker/result backend
- PostgreSQL metadata store
- Neo4j graph database

## AWS EC2 Deployment Notes

- use an EC2 instance with enough CPU and disk for video workloads
- attach an IAM role if using native AWS S3
- for MinIO or another S3-compatible store, set `STORAGE_ENDPOINT_URL`
- persist `/app/data` with an EBS volume or host bind mount
- place the YOLO weights where `MODEL_PATH` can access them, or let Ultralytics download them on first run

## Environment Variables

Key runtime settings:

- `DATABASE_URL`
- `BROKER_URL`
- `RESULT_BACKEND_URL`
- `STORAGE_BACKEND`
- `LOCAL_STORAGE_PATH`
- `UPLOAD_TEMP_PATH`
- `STORAGE_BUCKET`
- `STORAGE_ENDPOINT_URL`
- `MODEL_PATH`
- `CONFIDENCE_THRESHOLD`
- `FRAME_SKIP`
- `FRAME_RESIZE_WIDTH`
- `STATIONARY_FRAME_WINDOW`
- `STATIONARY_PIXEL_THRESHOLD`
- `TRACKER_MAX_DISTANCE`
- `PLATE_ENABLED`
- `ANPR_API_TOKEN`
- `GRAPH_ENABLED`
- `NEO4J_URI`

## Important Assumptions

- the refactor now uses Redis + Celery so the API and processing worker are deployed separately
- RTSP support is implemented through the same ingestion abstraction as file processing
- alert generation includes object detection events and stationary-object alerts; this is designed to be extended with domain-specific rules such as speeding or forbidden-zone alerts
- plate detection is opt-in and depends on an external ANPR provider token
- knowledge graph writes are opt-in and activate only when Neo4j settings are enabled
