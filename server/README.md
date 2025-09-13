# Mem0 REST API Server

Mem0 provides a REST API server (written using FastAPI). Users can perform all operations through REST endpoints. The API also includes OpenAPI documentation, accessible at `/docs` when the server is running.

## Features

- **Create memories:** Create memories based on messages for a user, agent, or run.
- **Retrieve memories:** Get all memories for a given user, agent, or run.
- **Search memories:** Search stored memories based on a query.
- **Update memories:** Update an existing memory.
- **Delete memories:** Delete a specific memory or all memories for a user, agent, or run.
- **Reset memories:** Reset all memories for a user, agent, or run.
- **OpenAPI Documentation:** Accessible via `/docs` endpoint.

## Running the server

You can run via Docker Compose using two modes:

- Fast runtime (default): uses `server/Dockerfile` and installs dependencies from `server/requirements.txt`.
  - docker compose -f server/docker-compose.yml up -d
  - Server: http://localhost:8000 (OpenAPI at /docs)

- Dev mode (library hot‑reload): compose override with `server/docker-compose.dev.yml`.
  - docker compose -f server/docker-compose.yml -f server/docker-compose.dev.yml up -d
  - Overrides only the dev bits (dev.Dockerfile, mounted volumes, reload)
  - Slower to build the first time (editable install), mais pratique pour itérer sur la lib.

Notes
- The default compose includes Qdrant and Memgraph services. Ensure their ports are free.
- For Docker for Windows, service names inside the container are `memory-qdrant` and `memory-memgraph` (the `/configure` endpoint normalizes these for you).
