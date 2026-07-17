# Kafka Backend

This backend is the Kafka version of the video analytics API/worker.

- API job submission publishes to Kafka topic `video_jobs`.
- Worker command is `python -m app.worker`.
- Video processing, storage, database writes, plate detection, graph writes, and API contracts remain aligned with the original backend.

Run it with:

```powershell
docker compose up --build
```
