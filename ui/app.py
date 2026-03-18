import streamlit as st
import cv2
import base64
import numpy as np
import time
from redis_reader import RedisReader
from visualizer import draw_tracks

st.set_page_config(layout="wide")

st.title("🚦 Traffic Intelligence Dashboard")

reader = RedisReader()

# Sidebar
st.sidebar.header("Controls")
camera_id = st.sidebar.selectbox("Camera", ["cam_1"])
st.sidebar.write("Status: 🟢 LIVE")

# Layout
col1, col2 = st.columns([3, 1])

frame_window = col1.empty()

metric1, metric2, metric3 = col2.columns(3)

events_container = st.container()
table_container = st.container()

while True:

    message = reader.get_latest_tracking()

    if not message or "frame" not in message:
        frame_window.write("Waiting for stream...")
        time.sleep(0.5)
        continue

    objects = message["objects"]

    # Decode frame
    frame_bytes = base64.b64decode(message["frame"])
    frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

    # Placeholder lookups
    plate_lookup = {}
    speed_lookup = {}

    frame = draw_tracks(frame, objects, plate_lookup, speed_lookup)

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_window.image(frame)

    # Metrics
    vehicle_count = len(objects)

    metric1.metric("Vehicles", vehicle_count)
    metric2.metric("Avg Speed", "—")
    metric3.metric("Congestion", "Normal")

    # Events
    with events_container:
        st.subheader("🚨 Recent Events")
        st.write("No critical events")

    # Table
    with table_container:
        st.subheader("🔍 Vehicle Insights")

        table_data = []

        for obj in objects:
            table_data.append({
                "Track ID": obj["track_id"],
                "Plate": plate_lookup.get(obj["track_id"], "—"),
                "Speed": speed_lookup.get(obj["track_id"], "—")
            })

        st.table(table_data)

    time.sleep(0.03)