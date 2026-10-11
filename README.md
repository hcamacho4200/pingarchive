**** This file is a draft ****

# PingArchive

PingArchive is a self-hosted network monitoring application that continuously
pings configured destinations, stores time-series measurements, and presents
latency, availability, and packet-loss history in a web dashboard.

The project separates packet collection, configuration, storage, and
visualization into independently deployable services. It can run locally for
development or as a Docker Compose stack.

## Features

- Monitor IPv4 addresses and hostnames at configurable ping intervals.
- Enable, disable, add, edit, and delete destinations from the UI.
- Record sent time, receive time, round-trip latency, timeouts, destination ID,
  destination name, target address, worker ID, and sequence number.
- View average latency, packet loss, and availability per destination.
- Explore latency history with TradingView Lightweight Charts.
- Select 5-minute, 1-hour, 24-hour, 7-day, and 30-day time ranges.
- Pan, zoom, pause live following, resume live updates, and hide individual
  destination series from the legend.
- Display outages as gaps instead of connecting the last successful samples.
- Filter and review recent timeout events.
- Reload destination configuration by restarting ping worker goroutines without
  stopping the Ping Engine process.
- Use light or dark mode.

## Architecture

```text
Browser
   |
   v
Nginx reverse proxy
   |-- / --------------------> React + TypeScript frontend
   `-- /api/v1/* ------------> FastAPI backend
                                  |-- configuration --> SQLite
                                  |-- measurements ---> QuestDB
                                  `-- control --------> Go Ping Engine
                                                           |
                                                           `--> ICMP targets
```

| Component | Technology | Responsibility |
| --- | --- | --- |
| `frontend/` | React, TypeScript, Vite/vinext, Lightweight Charts | Dashboard and settings UI |
| `backend/` | Python, FastAPI, SQLAlchemy, Alembic | REST API, destination configuration, measurement queries, and engine control proxy |
| `pingarchive-ping-engine/` | Go | ICMP send/receive workers, timeout detection, and QuestDB ingestion |
| QuestDB | Time-series database | Ping measurements and historical queries |
| SQLite | Relational database | Ping destination configuration |
| Nginx | Reverse proxy | Single production entry point for the UI and API |

## Repository Layout

```text
ping_archive/
├── backend/                    FastAPI service and database migrations
├── frontend/                   React/TypeScript user interface
├── pingarchive-ping-engine/    Go ICMP collection engine
├── docker-compose/             Production-style service orchestration
├── .vscode/                    Development launch configurations
├── FEATURES.md                 Release and feature notes
└── CONTRIBUTE.md               Development notes
```

## Requirements

For local development:

- Go 1.27 or newer
- Python 3.14.5
- Node.js 22.13 or newer
- Docker Desktop or Docker Engine for QuestDB and container deployment
- VS Code with the Go and Python debugging extensions if using the included
  compound launch configuration

## Local Development

### 1. Start QuestDB

From the repository root:

```bash
docker compose -f docker-compose/docker-compose.yml up -d questdb
```

QuestDB listens on port `9000` for HTTP/ILP traffic inside the current
configuration. Its persistent data directory is
`docker-compose/questdb/`.

### 2. Start the backend

```bash
cd backend
uv sync
uv run python src/main.py execute-api
```

The development API is available at `http://127.0.0.1:8002/api/v1`.
Database migrations are applied when the backend starts.

### 3. Start the frontend

```bash
cd frontend
npm ci
npm run dev -- --host
```

The development UI normally starts at `http://localhost:3000` and supports hot
reload.

### 4. Start the Ping Engine

```bash
cd pingarchive-ping-engine
go run .
```

On native macOS the engine uses an unprivileged `udp4` ICMP socket. In a Linux
container it uses raw ICMP and requires the `NET_RAW` capability.

### VS Code compound launch

Open the repository root in VS Code and run the `->Full Stack` compound launch
configuration. It starts the backend, frontend, and Ping Engine together.

## Configuration

The backend and Ping Engine read configuration from environment variables. The
development values are stored in `backend/.env`; the Ping Engine's `.env`
symlink points to the same file.

| Variable | Development value | Purpose |
| --- | --- | --- |
| `API_BIND_HOST` | `localhost` | Backend bind address; Ping Engine backend hostname |
| `API_BIND_PORT` | `8002` | Backend API port |
| `API_RELOAD` | `true` | Enable backend development reload |
| `API_WORKERS` | `1` | Uvicorn worker count |
| `DATABASE_URL` | `sqlite:///../data/pingarchive.db` | Configuration database |
| `PING_ENGINE_HOST` | `localhost` | Engine control hostname used by FastAPI |
| `PING_ENGINE_PORT` | `8100` | Engine control port used by FastAPI |
| `PING_CONTROL_SERVER_LISTEN_ADDRESS` | `127.0.0.1:8100` | Go control-server bind address |
| `QWEST_DB_ADDRESS` | `localhost:9000` | QuestDB address used by the application |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8002/api/v1` | Development browser API base URL |

In production, the frontend uses the same-origin `/api/v1` path. Nginx forwards
that path to the backend container, so the browser never needs direct access to
port `8002` or the Docker hostname `backend`.

## Docker Compose

The Compose stack contains:

- `proxy` — public entry point on `http://localhost:3001`
- `frontend` — internal port `3000`
- `backend` — internal port `8002`
- `engine` — internal control port `8100`, with `NET_RAW`
- `questdb` — internal QuestDB service

Start the stack with locally available images:

```bash
cd docker-compose
docker compose up -d
docker compose ps
```

Follow service logs:

```bash
docker compose logs -f frontend backend engine proxy questdb
```

Stop the stack:

```bash
docker compose down
```

Persistent SQLite and QuestDB data remain in their mounted directories after
the containers stop.

## Container Registry

Images can be published to GitHub Container Registry using names such as:

```text
ghcr.io/OWNER/pingarchive-frontend:VERSION
ghcr.io/OWNER/pingarchive-backend:VERSION
ghcr.io/OWNER/pingarchive-engine:VERSION
```

After replacing `OWNER` and `VERSION` in the Compose image entries:

```bash
docker login ghcr.io
docker compose pull
docker compose up -d
```

When publishing from Apple Silicon for both ARM and Intel/AMD hosts, build a
multi-platform image for `linux/arm64` and `linux/amd64`.

## Ping Engine Control

The backend proxies engine control requests rather than exposing the engine
control port publicly.

The **Restart Ping Engine** button does not terminate the Go process. It:

1. Loads the latest destinations from FastAPI.
2. Cancels the current per-destination ping workers.
3. Waits for those workers to exit.
4. Starts a new set of workers using the updated configuration.

The ICMP socket, receiver, timeout reaper, measurement processor, QuestDB
writer, and control server remain running during this operation.

## Tests and Checks

Run the component checks independently:

```bash
# Go engine
cd pingarchive-ping-engine
go test ./...

# Python backend
cd backend
uv run pytest
uv run ruff check src tests

# Frontend
cd frontend
npm test
npm run lint
```

Additional migration and contribution notes are available in
[`CONTRIBUTE.md`](CONTRIBUTE.md), and the feature history is recorded in
[`FEATURES.md`](FEATURES.md).

## Current Scope

PingArchive currently focuses on ICMP latency, timeout, packet-loss, and
availability monitoring. Traceroute scheduling, bandwidth testing, and
WebSocket-based streaming are potential future extensions rather than current
features.
