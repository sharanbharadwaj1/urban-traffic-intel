How to see it in DBeaver

Use these connection settings:

Host: localhost
Port: 5432
Database: trafficdb1
Username: traffic1
Password: traffic1
In DBeaver:

Database → New Database Connection
Choose PostgreSQL
Enter the values above
Test connection
Open:
Schemas
public
Tables
events
Useful queries:

SELECT * FROM events
ORDER BY created_at DESC
LIMIT 50;
SELECT event_type, count(*)
FROM events
GROUP BY event_type
ORDER BY count(*) DESC;
SELECT camera_id, track_id, event_type, plate, frame_id, created_at
FROM events
ORDER BY created_at DESC
LIMIT 100;
SELECT *
FROM events
WHERE plate IS NOT NULL
ORDER BY created_at DESC;