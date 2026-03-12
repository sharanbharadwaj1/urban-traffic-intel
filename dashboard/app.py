import streamlit as st
import redis
import json

r = redis.Redis(host="localhost", port=6379)

st.title("Urban Traffic Intelligence Dashboard")

st.header("Latest Tracked Objects")

messages = r.xrevrange("tracked_objects", count=5)

for msg_id, msg in messages:

    payload = json.loads(msg[b'payload'])

    st.json(payload)

st.header("Latest Detections")

messages = r.xrevrange("vision_detections", count=5)

for msg_id, msg in messages:

    payload = json.loads(msg[b'payload'])

    st.json(payload)


st.header("Track History")

keys = r.keys("track:*")

for key in keys[:5]:

    history = r.lrange(key, 0, -1)

    st.write(key.decode())

    for entry in history:

        st.json(json.loads(entry))