# Surveillance Tracker V2: Theory Notes and Interview Guide

## 1. What This Project Is

This project is a **distributed surveillance video analytics system** built as a pipeline of specialized services. It detects vehicles, tracks them across frames, detects operational events, reads license plates, stores structured records, and builds a knowledge graph for relationship-centric analysis.

Think of it as a practical application of:

- computer vision
- object tracking
- event-driven system design
- stream processing
- database design
- graph modeling
- dashboard engineering

## 2. Why This Project Matters

From an academic and interview perspective, this project is strong because it combines:

- real-time processing
- multi-service architecture
- multiple databases chosen by access pattern
- model integration and deployment constraints
- debugging under practical system limitations

It is not just “I used YOLO on a video.” It is a full system.

## 3. High-Level System Design

### Core Idea

Each service does one job well and communicates through Redis streams.

Pipeline:

1. `vision_service` detects raw vehicles
2. `tracking_service` turns detections into persistent tracks
3. `event_service` turns track behavior into semantic events
4. `plate_service` resolves identity through ANPR
5. `graph_service` builds relationships in Neo4j
6. `ui` presents the live operational state

### Why This Design Is Good

- clear separation of concerns
- easier debugging
- each service can be improved independently
- natural fit for event-driven architectures

## 4. Why Redis Was Used

Redis was selected for:

- fast stream transport
- simple producer-consumer communication
- lightweight caching for `plate:{track_id}`
- temporary deduplication keys

Conceptually:

- Redis handles the **hot path**
- PostgreSQL handles **durable structured records**
- Neo4j handles **relationship intelligence**

This is a strong interview talking point because it shows storage selection by workload.

## 5. Computer Vision Stage

### Detection

The system uses YOLO to detect objects in frames.

Input:

- video frames from MP4 or camera stream

Output:

- bounding boxes
- class IDs
- confidence scores

Why YOLO:

- fast enough for near-real-time inference
- strong baseline for vehicle detection
- easy model integration

### Important Theory

Object detection solves:

- **what** is present
- **where** it is present

But it does not solve:

- persistent identity across time

That is why tracking is needed.

## 6. Tracking Stage

### Purpose

Tracking links detections across frames so that the same physical vehicle keeps the same logical identity over time.

### Tracker Used

- ByteTrack through `supervision`

### Why Tracking Is Hard

Tracking fails when:

- detections flicker
- boxes shift
- objects overlap
- class labels change
- low-quality visuals reduce detector consistency

### What We Improved

The project initially depended too heavily on raw tracker IDs. That caused fragmentation where the same vehicle could appear as multiple track IDs.

Improvements added:

- duplicate suppression inside the same frame
- stable-ID mapping over raw ByteTrack IDs
- larger tolerance for reusing nearby tracks
- grouping of four-wheeler classes so `car` vs `truck` misclassification does not automatically split identity

### Interview Answer

If asked “Why was tracking unstable?”:

- low-quality video caused bounding-box jitter and intermittent detection drops
- tracker identity assignment is only as stable as detection continuity
- therefore we added a stable-ID layer and family-aware matching logic

## 7. Event Detection Stage

### What Event Detection Does

Tracking gives raw movement over time. Event detection converts that into useful semantics:

- vehicle is stopped
- vehicle is speeding
- scene is congested

### Core Idea

We maintain short track histories and compute motion-related features such as speed.

This is a classic transition:

- perception data
- to semantic interpretation

### Why This Matters

A surveillance system is more useful when it answers:

- what happened?

not just:

- what objects are visible?

## 8. Plate Recognition Stage

### Original Problem

Plate detection did not work reliably.

Observed issues:

- wrong crops
- OCR on weak regions
- stale or noisy reads
- bikes being processed even though front plates were not visible
- event timing not aligned with plate timing

### Why Generic OCR Was Not Enough

OCR alone is weak when:

- text is tiny
- the crop is misaligned
- motion blur exists
- perspective is poor
- the plate is partially occluded

### Why ANPR Was Chosen

Cloud ANPR proved to work on real live samples when generic OCR approaches did not.

This is an important lesson:

- the best model is not always the one with the most control
- sometimes a purpose-built service is more reliable than a local but brittle stack

### Important System Design Change

The system moved from:

- immediate one-shot plate reading

to:

- buffered per-track snapshot selection
- controlled retry logic
- eventual confirmation and persistence

### Additional Controls Added

- only one best snapshot per attempt
- retry cooldown frames
- ANPR request throttling
- backoff after `429`
- plate normalization and validity checks

## 9. Why the Knowledge Graph Was Added

### Traditional Database View

In a relational database, you store rows such as:

- event row
- camera row
- plate column

This is excellent for transactional storage.

### Graph View

A graph is stronger when the question is about relationships:

- which vehicle was seen at which camera?
- how many times?
- during which sighting interval?
- what connected observations belong together?

### Current Graph Model

Nodes:

- `Vehicle`
- `Sighting`
- `Camera`

Relationships:

- `(Vehicle)-[:OBSERVED_AS]->(Sighting)`
- `(Sighting)-[:AT_CAMERA]->(Camera)`
- `(Vehicle)-[:SEEN_AT]->(Camera)`

### Why This Is Good Modeling

- `Vehicle` stores persistent identity
- `Camera` stores observation location
- `Sighting` stores the temporal context

This is a very interview-friendly modeling choice.

## 10. Why the First Graph Attempt Failed

This is one of the strongest architectural lessons in the project.

### The Mistake

`graph_service` initially listened to `tracked_objects` and tried to fetch `plate:{track_id}` immediately.

Problem:

- plate detection usually completed later

Result:

- graph saw the vehicle before plate identity existed
- Neo4j stayed empty

### The Fix

`plate_service` was changed to publish a `vehicle_identity` stream after successful plate confirmation.

Then:

- `graph_service` consumed `vehicle_identity`
- each graph write happened only after identity was known

### Why This Matters

This is a classic distributed-systems lesson:

- event timing matters as much as data content

## 11. Databases Used and Why

### Redis

Use case:

- streams
- cache
- short-term coordination

Why:

- extremely fast
- ideal for event buses and small transient state

### PostgreSQL

Use case:

- structured `events` table

Why:

- reliable transactional store
- good for filtering, ordering, reporting, and tabular inspection

### Neo4j

Use case:

- identity and relationship graph

Why:

- graph queries are natural for surveillance intelligence

This multi-database design is a major interview strength.

## 12. Dashboard Design

The dashboard presents:

- live frame with annotated tracks
- recent operational events
- vehicle insights table
- knowledge graph sightings in GMT

### Why GMT Was Used

GMT or UTC removes ambiguity across environments and is good practice for logs, persistence, and cross-region interpretation.

## 13. Major Challenges and How They Were Overcome

### Challenge: Plate Not Detected Reliably

Root causes:

- weak OCR input
- wrong or low-quality crops
- timing mismatch between tracking and plate identity

Resolution:

- moved to cloud ANPR
- added retry and buffering logic
- published identity after confirmation

### Challenge: API Rate Limits

Root cause:

- free-tier ANPR had strict call limits

Resolution:

- cooldown frames
- one snapshot per attempt
- global throttling and backoff

### Challenge: Duplicate Track IDs for Same Vehicle

Root cause:

- detection jitter
- label flips
- overlap and occlusion

Resolution:

- stable-ID logic
- class-family grouping
- duplicate suppression

### Challenge: Graph Empty Despite Working Plates

Root cause:

- graph was reading the wrong stream at the wrong time

Resolution:

- introduced `vehicle_identity` stream

### Challenge: Invalid Plates Like Short Junk Reads

Root cause:

- noisy detections and weak OCR candidates

Resolution:

- normalized and validated candidate strings before storing

## 14. Recent Implementation Milestones

The current state of the project includes:

- surveillance-oriented repositioning
- stable tracking improvements
- ANPR-based plate detection
- PostgreSQL event persistence
- Neo4j knowledge graph integration
- dashboard graph visibility with GMT formatting

These recent changes are important because they show iterative product maturity, not just code churn.

## 15. Interview Preparation Notes

### How to Describe the Project in One Minute

“Surveillance Tracker V2 is a multi-service video analytics system that processes camera frames, detects and tracks vehicles, identifies operational events such as speeding or stopping, resolves license plates using ANPR, stores structured events in PostgreSQL, and builds a vehicle-camera-sighting knowledge graph in Neo4j. The services communicate through Redis streams, and the system is visualized through a Streamlit dashboard.”

### Likely Interview Questions

#### Q1. Why use microservices instead of a monolith?

Good answer:

- separate CPU-intensive inference from tracking, eventing, graph updates, and UI
- easier debugging and replacement of components
- more natural for stream-based workflows

#### Q2. Why use three databases?

Good answer:

- Redis for streaming and transient state
- PostgreSQL for durable tabular event history
- Neo4j for relationship-centric investigation queries

#### Q3. Why did graph ingestion initially fail?

Good answer:

- graph depended on track stream timing instead of identity-confirmed timing
- plate identity arrived later
- fixed by introducing a post-confirmation identity stream

#### Q4. Why was tracking fragmented?

Good answer:

- tracking depends on detection stability
- low-quality video and class jitter caused identity fragmentation
- fixed partially with stable-ID remapping and duplicate suppression

#### Q5. Why choose ANPR over local OCR?

Good answer:

- empirical reliability on live samples was better
- local OCR path was too brittle for the available image quality
- ANPR reduced engineering uncertainty for the prototype

#### Q6. What are the limitations?

Good answer:

- occlusion still causes occasional mis-association
- free-tier ANPR rate limits throughput
- true multi-camera re-identification is not yet implemented

## 16. Concepts to Revise for Interviews

If using this project for interview prep, revise:

- object detection vs tracking
- IoU and why it matters
- stream processing basics
- cache vs database roles
- eventual consistency
- graph data modeling
- schema design in PostgreSQL
- rate limiting and backoff strategies
- microservice orchestration basics

## 17. Quick Revision Summary

Remember these one-liners:

- YOLO solves detection, not persistent identity.
- Tracking is only as stable as the detections it receives.
- Redis is the event bus.
- PostgreSQL is the audit/event store.
- Neo4j is the relationship layer.
- Graph ingestion must happen after identity is known.
- ANPR reliability beat local OCR for this prototype.
- GMT is used in the dashboard to keep timestamps unambiguous.

## 18. Final Student Takeaway

This project is a strong example of how real-world systems rarely fail because of one isolated model. They fail because of:

- timing
- data quality
- storage boundaries
- service coordination
- operational assumptions

Understanding and fixing those interactions is what turns a demo into an engineering project.

