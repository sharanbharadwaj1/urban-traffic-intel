# Kafka Pipeline

This folder is a Kafka-based copy of the original event-driven traffic pipeline.
The original Redis/Celery implementation remains untouched outside this folder.

## What Changed

- Redis Streams were replaced by Kafka topics:
  - `vision_detections`
  - `tracked_objects`
  - `plate_events`
  - `vehicle_identity`
  - `ui_events`
- Redis plate cache was replaced by the compacted Kafka topic `vehicle_plate_cache`.
- Redis TTL keys used for duplicate event and plate-request suppression are now local TTL stores inside `event_service`.
- Redis-backed track history is now local in-memory state inside `event_service`.
- Celery job dispatch in `backend` was replaced by Kafka topic `video_jobs`; `python -m app.worker` consumes jobs and calls the same video-processing logic.

## Run The Service Pipeline

Start Kafka:

```powershell
docker compose -f kafka_pipeline/docker-compose.yml up -d
```

Install the Kafka client dependency in your Python environment:

```powershell
pip install -r kafka_pipeline/requirements.txt
```

Place the required local model weights in the same locations used by the original pipeline, for example `vision_service/yolov8n.pt` and the plate-service `.pt` files, or rely on the configured model provider to download public weights. Model binaries and `.env` files are intentionally ignored in this Kafka copy.

Run the pipeline:

```powershell
python kafka_pipeline/runner/run_pipeline.py
```

## Run The Backend

From `kafka_pipeline/backend`:

```powershell
docker compose up --build
```

The API still exposes the same use case. Uploads create queued jobs, and the worker processes videos out of band; Kafka now carries the job messages instead of Celery/Redis.
