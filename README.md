# Surveillance Tracker V2

Surveillance Tracker V2 is a multi-service vehicle monitoring platform that processes video feeds, tracks vehicles across frames, detects stopped and speeding behavior, resolves visible number plates, stores structured events, builds a Neo4j knowledge graph, and displays the results in a live Streamlit dashboard.

## Highlights

- YOLO-based vehicle detection
- ByteTrack-based multi-object tracking with stable-ID enhancements
- stopped and speeding event detection
- ANPR-driven plate recognition for eligible four-wheelers
- Redis stream-based service communication
- PostgreSQL event persistence
- Neo4j knowledge graph with `Vehicle`, `Sighting`, and `Camera`
- dashboard section for graph-backed sightings in GMT

## Active Pipeline

```text
Video -> vision_service -> tracking_service -> event_service -> plate_service -> graph_service -> UI
```

Redis streams used in the current flow:

- `vision_detections`
- `tracked_objects`
- `plate_events`
- `ui_events`
- `vehicle_identity`

## Repository Structure

- [vision_service](/E:/Projects%20Urban%20Traffic%20Intel%20System/traffic-ai-platform/vision_service): frame ingestion and YOLO detection
- [tracking_service](/E:/Projects%20Urban%20Traffic%20Intel%20System/traffic-ai-platform/tracking_service): track generation and stable-ID logic
- [event_service](/E:/Projects%20Urban%20Traffic%20Intel%20System/traffic-ai-platform/event_service): motion analysis and event generation
- [plate_service](/E:/Projects%20Urban%20Traffic%20Intel%20System/traffic-ai-platform/plate_service): plate confirmation, identity publishing, and event enrichment
- [graph_service](/E:/Projects%20Urban%20Traffic%20Intel%20System/traffic-ai-platform/graph_service): Neo4j knowledge graph writer
- [ui](/E:/Projects%20Urban%20Traffic%20Intel%20System/traffic-ai-platform/ui): Streamlit dashboard
- [models](/E:/Projects%20Urban%20Traffic%20Intel%20System/traffic-ai-platform/models): database schema
- [infra](/E:/Projects%20Urban%20Traffic%20Intel%20System/traffic-ai-platform/infra): Redis, PostgreSQL, and Neo4j containers
- [runner](/E:/Projects%20Urban%20Traffic%20Intel%20System/traffic-ai-platform/runner): local pipeline bootstrap
- [docs](/E:/Projects%20Urban%20Traffic%20Intel%20System/traffic-ai-platform/docs): project and theory documentation

## Infrastructure

Start backing services:

```powershell
docker compose -f infra\docker-compose.yml up -d
```

This starts:

- Redis on `6379`
- PostgreSQL on `5432`
- Neo4j Browser on `7474`
- Neo4j Bolt on `7687`

## Local Run

Run the pipeline:

```powershell
cd runner
python run_pipeline.py
```

The runner starts:

- `vision_service`
- `tracking_service`
- `plate_service`
- `event_service`
- `graph_service`
- Streamlit UI

## Storage Roles

### Redis

- inter-service streaming
- transient caching
- request throttling and deduplication

### PostgreSQL

- durable `events` table
- structured storage for stopped, speeding, and congestion events
- later enrichment with resolved plates

### Neo4j

- surveillance knowledge graph
- stores vehicle-camera-sighting relationships

## Neo4j Access

Open:

- [http://localhost:7474](http://localhost:7474)

Default local credentials:

- user: `neo4j`
- password: `password`

Useful query:

```cypher
MATCH (v:Vehicle)-[:OBSERVED_AS]->(s:Sighting)-[:AT_CAMERA]->(c:Camera)
RETURN v, s, c
LIMIT 50
```

## PostgreSQL Access

Use DBeaver or another SQL client with:

- host: `localhost`
- port: `5432`
- database: `trafficdb1`
- user: `traffic1`
- password: `traffic1`

Useful query:

```sql
SELECT *
FROM events
ORDER BY created_at DESC
LIMIT 50;
```

## Current Limitations

- severe occlusion can still cause temporary plate-to-track mis-association
- low-quality footage can still fragment tracks
- free-tier ANPR rate limiting restricts throughput
- graph is currently optimized for single-camera surveillance flow

## Documentation

- professional system documentation: [docs/PROJECT_DOCUMENTATION.md](/E:/Projects%20Urban%20Traffic%20Intel%20System/traffic-ai-platform/docs/PROJECT_DOCUMENTATION.md)
- theory and interview guide: [docs/STUDENT_THEORETICAL_NOTES.md](/E:/Projects%20Urban%20Traffic%20Intel%20System/traffic-ai-platform/docs/STUDENT_THEORETICAL_NOTES.md)

## Future Scope

- multi-camera identity correlation
- watchlist and blacklist management
- alerting workflows for suspicious vehicles
- graph-driven investigation queries in the dashboard
- richer event graph modeling for speeding, stopping, and congestion
- operator search by plate, camera, or time range
- replay support and incident review workflow
- stronger local plate detection fallback for offline environments
- API gateway and secure user authentication for production use
