CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    camera_id TEXT NOT NULL,
    track_id BIGINT,
    event_type TEXT NOT NULL,
    plate TEXT,
    frame_id BIGINT,
    event_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_camera_created_at
    ON events (camera_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_events_event_type_created_at
    ON events (event_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_events_track_id
    ON events (track_id);

CREATE INDEX IF NOT EXISTS idx_events_plate
    ON events (plate);
