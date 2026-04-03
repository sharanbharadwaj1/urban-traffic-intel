Useful queries from here:

MATCH (v:Vehicle)-[:OBSERVED_AS]->(s:Sighting)-[:AT_CAMERA]->(c:Camera)
RETURN v, s, c
LIMIT 50
MATCH (v:Vehicle)-[r:SEEN_AT]->(c:Camera)
RETURN v.plate, c.id, r.first_seen_at, r.last_seen_at, r.total_sightings
ORDER BY r.last_seen_at DESC
MATCH (v:Vehicle)
RETURN v.plate
ORDER BY v.plate
MATCH (c:Camera)<-[:AT_CAMERA]-(s:Sighting)<-[:OBSERVED_AS]-(v:Vehicle)
RETURN c.id, v.plate, s.track_id, s.frames_seen, s.last_seen_at
ORDER BY s.last_seen_at DESC