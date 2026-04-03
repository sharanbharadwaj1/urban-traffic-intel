import base64
import time

import cv2
import numpy as np
import streamlit as st

from graph_reader import GraphReader
from redis_reader import RedisReader
from visualizer import draw_tracks


st.set_page_config(
    page_title="Surveillance Dashboard",
    layout="wide",
)


@st.cache_resource
def get_reader():
    return RedisReader()


@st.cache_resource
def get_graph_reader():
    return GraphReader()


def decode_frame(frame_base64):
    frame_bytes = base64.b64decode(frame_base64)
    frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
    return cv2.imdecode(frame_array, cv2.IMREAD_COLOR)


def build_speed_lookup(events):
    speed_lookup = {}

    for event in events:
        track_id = event.get("track_id")
        speed = event.get("speed")

        if track_id is None or speed is None:
            continue

        speed_lookup[track_id] = speed

    return speed_lookup


def format_event(event):
    event_type = event.get("event_type", "unknown")
    track_id = event.get("track_id")
    plate = event.get("plate") or "unknown"

    if event_type == "vehicle_stopped":
        return "error", f"Stopped vehicle | Track {track_id} | Plate {plate}"

    if event_type == "vehicle_speeding":
        speed = event.get("speed", "n/a")
        return "warning", f"Speeding vehicle | Track {track_id} | Speed {speed} | Plate {plate}"

    if event_type == "traffic_congestion":
        count = event.get("vehicle_count", "n/a")
        return "info", f"Traffic congestion | Vehicles {count}"

    return "write", str(event)


reader = get_reader()
graph_reader = get_graph_reader()

if "event_cache" not in st.session_state:
    st.session_state.event_cache = {}


st.title("Traffic Intelligence Dashboard")

camera_options = reader.get_camera_ids() or ["cam_1"]

st.sidebar.header("Controls")
selected_camera = st.sidebar.selectbox("Camera", camera_options)
auto_refresh = st.sidebar.toggle("Auto refresh", value=True)
refresh_interval = st.sidebar.slider("Refresh interval (ms)", 500, 5000, 1000, 250)
st.sidebar.write("Status: LIVE")

message = reader.get_latest_tracking(selected_camera)
events = reader.get_latest_events(selected_camera, count=20)

camera_event_cache = st.session_state.event_cache.setdefault(selected_camera, {})
for event in events:
    camera_event_cache[event["redis_id"]] = event

recent_events = list(camera_event_cache.values())
recent_events.sort(key=lambda item: item["redis_id"], reverse=True)
recent_events = recent_events[:10]
st.session_state.event_cache[selected_camera] = {
    event["redis_id"]: event for event in recent_events
}

if not message or "frame" not in message:
    st.warning(f"Waiting for tracked frames from {selected_camera}.")
    if auto_refresh:
        time.sleep(refresh_interval / 1000)
        st.rerun()
    st.stop()

objects = message.get("objects", [])
track_ids = [obj.get("track_id") for obj in objects if obj.get("track_id") is not None]
plate_lookup = reader.get_plate_lookup(track_ids)
speed_lookup = build_speed_lookup(recent_events)

frame = decode_frame(message["frame"])

if frame is None:
    st.error("Latest frame could not be decoded.")
    st.stop()

frame = draw_tracks(frame, objects, plate_lookup, speed_lookup)
frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

speeding_count = sum(1 for event in recent_events if event.get("event_type") == "vehicle_speeding")
stopped_count = sum(1 for event in recent_events if event.get("event_type") == "vehicle_stopped")
congestion_active = any(event.get("event_type") == "traffic_congestion" for event in recent_events)

media_col, side_col = st.columns([3, 2])

with media_col:
    st.image(frame, channels="RGB", width="stretch")

with side_col:
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Vehicles", len(objects))
    metric_col2.metric("Speeding", speeding_count)
    metric_col3.metric("Stopped", stopped_count)
    st.caption(f"Congestion: {'Detected' if congestion_active else 'Normal'}")
    st.caption(f"Frame ID: {message.get('frame_id', 'n/a')}")

st.subheader("Recent Events")

if not recent_events:
    st.info("No recent events for this camera.")
else:
    for event in recent_events:
        level, text = format_event(event)

        if level == "error":
            st.error(text)
        elif level == "warning":
            st.warning(text)
        elif level == "info":
            st.info(text)
        else:
            st.write(text)

st.subheader("Vehicle Insights")

table_data = []
for obj in objects:
    track_id = obj.get("track_id")
    speed_value = speed_lookup.get(track_id)
    table_data.append(
        {
            "Track ID": track_id,
            "Plate": plate_lookup.get(track_id) or "",
            "Speed (px/s)": float(speed_value) if speed_value is not None else None,
            "Class ID": obj.get("class_id"),
            "Confidence": round(float(obj.get("confidence", 0)), 3),
        }
    )

if table_data:
    st.dataframe(table_data, width="stretch", hide_index=True)
else:
    st.info("No tracked objects in the latest frame.")

st.subheader("VEHICLE SIGHTINGS: ")

try:
    sightings = graph_reader.get_camera_sightings(selected_camera, limit=10)
except Exception as exc:
    sightings = []
    st.warning(f"Knowledge graph unavailable: {exc}")

if sightings:
    for sighting in sightings:
        st.caption(
            f"Vehicle {sighting['plate']} seen at {sighting['camera_id']} "
            f"from {sighting['first_seen_at']} to {sighting['last_seen_at']}"
        )

    st.dataframe(
        [
            {
                "Plate": sighting["plate"],
                "Camera": sighting["camera_id"],
                "First Seen (GMT)": sighting["first_seen_at"],
                "Last Seen (GMT)": sighting["last_seen_at"],
                "Sightings": sighting["total_sightings"],
            }
            for sighting in sightings
        ],
        width="stretch",
        hide_index=True,
    )
else:
    st.info("No knowledge graph sightings available for this camera yet.")

if auto_refresh:
    time.sleep(refresh_interval / 1000)
    st.rerun()
