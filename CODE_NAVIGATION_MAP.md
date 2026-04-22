# Code Navigation Map

This guide is a code-reading map for the current `traffic-ai-platform` backend refactor. Use it to understand where to start, which files matter most, and how the runtime flow moves through the codebase.

## Best Reading Order

If you want the shortest path to understanding the whole system, read these files in this order:

1. [backend/app/api/routes.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/api/routes.py)
2. [backend/app/services/jobs.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/jobs.py)
3. [backend/app/worker.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/worker.py)
4. [backend/app/services/dependencies.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/dependencies.py)
5. [backend/app/services/video_ingestion.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/video_ingestion.py)
6. [backend/app/services/frame_pipeline.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/frame_pipeline.py)
7. [backend/app/services/inference.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/inference.py)
8. [backend/app/services/tracking.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/tracking.py)
9. [backend/app/services/alerts.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/alerts.py)
10. [backend/app/services/plates.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/plates.py)
11. [backend/app/services/graph.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/graph.py)
12. [backend/app/db/models.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/db/models.py)
13. [backend/app/repositories/jobs.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/repositories/jobs.py)
14. [backend/app/repositories/events.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/repositories/events.py)
15. [backend/app/ui.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/ui.py)

If you read only three files first, make them:

- [backend/app/api/routes.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/api/routes.py)
- [backend/app/services/jobs.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/jobs.py)
- [backend/app/worker.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/worker.py)

---

## Folder Map

### `backend/app/api`

Purpose:

- HTTP endpoints
- request validation
- response delivery
- dashboard route

Main file:

- [backend/app/api/routes.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/api/routes.py)

Use this folder when you want to answer:

- What endpoints exist?
- Which service method does an endpoint call?
- Where does `/upload-video` start?
- Where does `/jobs/{job_id}/live-state` come from?

### `backend/app/core`

Purpose:

- runtime settings
- logging

Files:

- [backend/app/core/config.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/core/config.py)
- [backend/app/core/logging.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/core/logging.py)

Use this folder when you want to answer:

- Which environment variables control the system?
- Where is Redis configured?
- Where are Neo4j and ANPR settings defined?
- How is logging formatted?

### `backend/app/db`

Purpose:

- ORM base
- database session
- table definitions

Files:

- [backend/app/db/base.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/db/base.py)
- [backend/app/db/session.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/db/session.py)
- [backend/app/db/models.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/db/models.py)

Use this folder when you want to answer:

- What is stored in the database?
- What fields does a `ProcessingJob` have?
- What fields does an `EventRecord` have?

### `backend/app/repositories`

Purpose:

- DB access helpers
- keep SQLAlchemy operations out of routes

Files:

- [backend/app/repositories/jobs.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/repositories/jobs.py)
- [backend/app/repositories/events.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/repositories/events.py)

Use this folder when you want to answer:

- How are jobs created and updated?
- How are events listed?
- How is plate data backfilled into old events?

### `backend/app/schemas`

Purpose:

- API response models

Main file:

- [backend/app/schemas/api.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/schemas/api.py)

Use this when you want to answer:

- What does `/jobs/{id}` return?
- What does `/events` return?
- What does `/jobs/{id}/live-state` return?

### `backend/app/services`

Purpose:

- all application logic
- pipeline execution
- storage
- inference
- alerts
- plates
- graph writes

This is the most important folder in the backend.

### `backend/app/ui.py`

Purpose:

- browser dashboard HTML and JavaScript
- live surveillance-style frontend

Use this when you want to answer:

- How does the dashboard poll the API?
- Which endpoints feed the UI?
- How is the live frame shown?

### `backend/app/worker.py`

Purpose:

- Celery app
- background task registration

Use this when you want to answer:

- Where does Celery start?
- What task is executed by the worker?

---

## Runtime Entry Points

### 1. FastAPI App Entry

File:

- [backend/app/main.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/main.py)

What happens here:

- settings are loaded
- logging is configured
- DB tables are created
- service container is created
- `/assets` is mounted for snapshots/live frames
- API router is included

Think of `main.py` as:

```text
Application bootstrap
```

### 2. API Entry

File:

- [backend/app/api/routes.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/api/routes.py)

Important routes:

- `/`
- `/health`
- `/upload-video`
- `/jobs`
- `/jobs/{job_id}`
- `/jobs/{job_id}/live-state`
- `/events`

Think of `routes.py` as:

```text
Public entrypoint into the backend
```

### 3. Worker Entry

File:

- [backend/app/worker.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/worker.py)

Important function:

- `process_video_job(job_id)`

Think of `worker.py` as:

```text
Background execution entrypoint
```

---

## Main Code Flow

## Flow A: Upload Request

When a user uploads a file or submits RTSP:

1. request enters [backend/app/api/routes.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/api/routes.py)
2. route calls `JobService.create_file_job()` or `JobService.create_rtsp_job()`
3. job is saved to DB
4. Celery task is enqueued
5. API returns job metadata immediately

The key file for this whole flow is:

- [backend/app/services/jobs.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/jobs.py)

### Methods to read first in `jobs.py`

- `create_file_job`
- `create_rtsp_job`
- `_create_job`
- `enqueue_job`

Those methods explain:

- where uploads are stored
- when DB rows are created
- when Redis/Celery is used

---

## Flow B: Worker Execution

After the task is queued:

1. Celery worker receives `job_id`
2. worker creates a fresh `ServiceContainer`
3. worker calls `JobService.process_job(job_id)`
4. `process_job` runs the full analytics loop

This is the most important single method in the system:

- `JobService.process_job`

If you understand that method, you understand most of the backend.

### Inside `process_job`

Read it in this order:

1. job status update to `running`
2. source open
3. frame loop
4. preprocess
5. inference
6. tracking
7. plate detection
8. alert generation
9. event persistence
10. live frame persistence
11. completion/failure handling

---

## Pipeline Services Map

### `video_ingestion.py`

File:

- [backend/app/services/video_ingestion.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/video_ingestion.py)

What it does:

- open a file or RTSP source with OpenCV
- yield frames one by one
- close the capture

Read this when you want to know:

- How does the worker read the uploaded video?
- How does RTSP get opened?

### `frame_pipeline.py`

File:

- [backend/app/services/frame_pipeline.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/frame_pipeline.py)

What it does:

- frame skipping
- optional resizing
- frame timestamp packaging

Read this when you want to know:

- Where are frames filtered?
- Where is preprocessing applied?

### `inference.py`

File:

- [backend/app/services/inference.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/inference.py)

What it does:

- lazy-load YOLO
- run inference
- map detections to structured objects
- log inference timing and classes

Read this when you want to know:

- Where is the model loaded?
- Where does confidence threshold apply?
- What is a `Detection`?

### `tracking.py`

File:

- [backend/app/services/tracking.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/tracking.py)

What it does:

- assign stable-ish track IDs
- match detections across frames

Read this when you want to know:

- How are track IDs created?
- What is a `TrackedObject`?

### `alerts.py`

File:

- [backend/app/services/alerts.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/alerts.py)

What it does:

- convert tracked objects into event objects
- currently generates:
  - `object_detected`
  - `stationary_object`

Read this when you want to know:

- Where do event types come from?
- What logic triggers a stationary alert?

### `plates.py`

File:

- [backend/app/services/plates.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/plates.py)

What it does:

- manage track snapshot buffers
- retry ANPR
- normalize plate strings
- confirm plates after enough reads

Read this when you want to know:

- How does ANPR get called?
- Why does a plate not appear immediately?
- How are retries and confirmation handled?

### `graph.py`

File:

- [backend/app/services/graph.py](/E:/Projects/Urban%20Traffic%20System/traffic-ai-platform/backend/app/services/graph.py)

What it does:

- connect to Neo4j if enabled
- create constraints
- `MERGE` vehicle/camera/sighting data

Read this when you want to know:

- When are graph writes triggered?
- How are sightings modeled?

### `storage.py`

File:

- [backend/app/services/storage.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/storage.py)

What it does:

- store uploaded video
- store JPEG snapshots
- store JSON live state
- switch between local and S3-compatible storage

Read this when you want to know:

- Where does `live/<job_id>/latest.jpg` come from?
- Where do event snapshots go?

---

## Live Dashboard Flow

The dashboard lives in:

- [backend/app/ui.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/ui.py)

### What the UI polls

- `/health`
- `/jobs`
- `/jobs/{job_id}`
- `/jobs/{job_id}/live-state`
- `/events`

### What the worker produces for the UI

Inside `JobService.process_job`, the worker also writes:

- live preview image
- live state JSON
- event snapshots

The helper responsible for this is:

- `_store_live_preview`

If you want to understand the live surveillance screen, read:

1. `routes.py`
2. `jobs.py` -> `_store_live_preview`
3. `ui.py`

---

## Data Flow Map

### Jobs

Main model:

- `ProcessingJob`

Flow:

- created by API
- updated by worker
- read by API/UI

### Events

Main model:

- `EventRecord`

Flow:

- created during processing
- plate can be backfilled later
- read by API/UI

### Live Preview

Files written by worker:

- `live/<job_id>/latest.jpg`
- `live/<job_id>/state.json`

Served through:

- `/assets/...`
- `/jobs/{job_id}/live-state`

### Snapshots

Files written by worker:

- `snapshots/<job_id>/...jpg`

These show up in event metadata and in the evidence gallery.

---

## “If You Want To Change X, Go Here”

### Add a new API route

Start in:

- [backend/app/api/routes.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/api/routes.py)

### Add a new config variable

Start in:

- [backend/app/core/config.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/core/config.py)
- [backend/.env.example](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/.env.example)

### Change model/inference behavior

Start in:

- [backend/app/services/inference.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/inference.py)

### Change tracking behavior

Start in:

- [backend/app/services/tracking.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/tracking.py)

### Add new alert types

Start in:

- [backend/app/services/alerts.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/alerts.py)

### Change plate logic

Start in:

- [backend/app/services/plates.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/plates.py)

### Change graph modeling

Start in:

- [backend/app/services/graph.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/graph.py)

### Change job lifecycle

Start in:

- [backend/app/services/jobs.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/services/jobs.py)
- [backend/app/repositories/jobs.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/repositories/jobs.py)

### Change what the dashboard shows

Start in:

- [backend/app/ui.py](/E:/Projects/Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/app/ui.py)

---

## Mental Model For Fast Understanding

Use this mental model while reading:

```text
routes.py
    -> receives request
    -> calls JobService

worker.py
    -> receives background task
    -> calls JobService.process_job

jobs.py
    -> orchestrates everything
    -> calls all pipeline services

services/*
    -> do the actual work

repositories/*
    -> talk to the DB

ui.py
    -> reads API outputs and renders the dashboard
```

If you remember only one sentence:

```text
JobService is the center of the code flow.
```

---

## Recommended Self-Study Path

### Round 1: Architecture reading

Read:

- `main.py`
- `routes.py`
- `worker.py`
- `dependencies.py`

Goal:

- understand how the app boots
- understand how API and worker connect

### Round 2: Processing reading

Read:

- `jobs.py`
- `video_ingestion.py`
- `frame_pipeline.py`
- `inference.py`
- `tracking.py`
- `alerts.py`
- `plates.py`

Goal:

- understand the surveillance pipeline

### Round 3: Persistence and UI

Read:

- `db/models.py`
- `repositories/jobs.py`
- `repositories/events.py`
- `storage.py`
- `ui.py`

Goal:

- understand what is stored
- understand how the dashboard gets its data

---

## Related Reference Docs

- [docs/PRODUCTION_BACKEND_ARCHITECTURE.md](/E:/Projects%20Urban%20Traffic%20Intel%20System/traffic-ai-platform/docs/PRODUCTION_BACKEND_ARCHITECTURE.md)
- [backend/README.md](/E:/Projects%20Urban%20Traffic%20Intel%20System/traffic-ai-platform/backend/README.md)

