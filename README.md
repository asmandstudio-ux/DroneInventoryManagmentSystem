# Drone Inventory Management System

A warehouse drone scanning platform with:
- FastAPI backend (JWT auth + RBAC, missions, scan results, reports)
- Postgres data store
- S3-compatible object storage (MinIO for local dev) for evidence and report artifacts
- Background worker for scan/report jobs
- Next.js dashboard for operations

## Local development (Docker)

1. Create an environment file:
   - Copy `.env.example` to `.env` and edit values if needed.

2. Start the stack:
   - `docker compose up --build`

3. Open:
   - Dashboard: `http://localhost:3000`
   - API docs: `http://localhost:8000/docs`
   - API health: `http://localhost:8000/health`
   - API readiness: `http://localhost:8000/ready`
   - MinIO console: `http://localhost:9001`

The dev compose runs the API and worker containers with source mounts and enables MinIO bucket init automatically.

## Production-like (Docker Compose)

Use `docker-compose.prod.yml`:
- Requires non-default secrets for Postgres, MinIO, and JWT.
- Runs database migrations as a one-shot `migrate` service before starting API/worker.
- Runs Next.js in production mode (built image).

Example:
- `docker compose -f docker-compose.prod.yml up --build`

## One-click start (Windows release bundle)

If you’re using the packaged Windows release zip from `dist/`:

1. Unzip `droneims-release_<version>.zip`
2. Double-click `DroneIMS.cmd`
   - Starts Docker Compose services
   - Opens the Dashboard login page: `http://localhost:3000/login`
   - Creates Desktop + Start Menu shortcuts named `DroneIMS` (first run)

More details are in [release/README.md](file:///c:/Users/asman/Desktop/DroneInventoryManagmentSystem/release/README.md).

## Core flows

- Auth:
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `GET /api/v1/auth/me`
- Missions:
  - `POST /api/v1/missions`
  - `GET /api/v1/missions`
  - `GET /api/v1/missions/{missionId}`
- Evidence upload:
  - `POST /api/v1/uploads/presign` returns a presigned PUT URL and server-minted object key for a scan result
  - Client uploads evidence bytes to S3 via PUT
  - `POST /api/v1/uploads/confirm` confirms the upload and (optionally) auto-enqueues scan processing
- Scan results:
  - `POST /api/v1/scan-results` stores scan metadata (mission link, drone id, data)
  - `POST /api/v1/scan-results/{scanResultId}/process` enqueues scan processing explicitly (if not auto-enqueued)
- Reports:
  - `POST /api/v1/reports` enqueues a report job
  - `GET /api/v1/reports/{jobId}/download` presigns a download URL when ready

## Testing

The API tests expect a reachable Postgres database (CI uses a service container).

1. Install:
   - `pip install -r requirements.txt -r requirements-dev.txt`

2. Set env:
   - `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/droneims_test`

3. Run:
   - `pytest -q`

### Frontend checks (no local Node)

If you don’t have Node/npm installed locally, run the dashboard checks inside the `dashboard` container (requires Docker Desktop / Docker daemon running):
- `docker compose run --rm dashboard npm run lint`
- `docker compose run --rm dashboard npm run build`

## Notes

- The worker currently drains queued jobs directly from Postgres; Redis is provisioned for future queue adoption but is not required by the current worker implementation.
