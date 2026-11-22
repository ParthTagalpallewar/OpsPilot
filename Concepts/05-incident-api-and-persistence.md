# Incident intake and persistence

An incident is the description submitted by an operator. An investigation is a run that collects evidence and builds a report. OpsPilot assigns each its own ID so a client can refer to the exact report it received.

The local replay API validates input before it reads the capture. It returns HTTP 201 when it has saved the completed investigation. The planned worker API uses HTTP 202 to acknowledge a request whose investigation will finish later.

SQLite stores the report in a local database file. The transaction commits the completed report as one unit. If reading the capture fails, no row is inserted. An HTTP client can retrieve the report after the API restarts, provided the restarted process points to the same file. This local design stores one JSON document per investigation. The planned PostgreSQL schema supports sharing state across workers and querying individual evidence records.

## Practice

Start the local API following the repository README. Submit a replay, save the investigation ID, restart the server, and retrieve the same report. Then submit a request with a blank title and compare the validation response with a lookup for an unknown ID.
