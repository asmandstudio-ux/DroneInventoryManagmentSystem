# Standalone Release Bundle

This folder lets you ship the application as an installable “bundle” using Docker Desktop (recommended).

What users get:
- A double-click install/start experience on Windows (`DroneIMS.cmd`)
- A running Dashboard + API + Postgres + MinIO on the user’s machine
- A feature overview and vendor comparison: `FEATURES_AND_COMPARISON.md`

## For you (the maintainer)

### 1) Build images + export offline tarballs

Requirements:
- Docker Desktop installed and running

From the repo root:

```powershell
.\release\build-images.ps1 -Version 1.0.0
```

This creates:
- `release/images/droneims-backend_1.0.0.tar`
- `release/images/droneims-worker_1.0.0.tar` (optional service)
- `release/images/droneims-dashboard_1.0.0.tar`

### 2) Create a distributable zip

```powershell
.\release\package.ps1 -Version 1.0.0
```

Output:
- `dist/droneims-release_1.0.0.zip`

### 3) Send the zip to users

Users install by double-clicking `DroneIMS.cmd`.

## For end users (Windows)

Requirements:
- Docker Desktop installed and running

Steps:
1) Unzip `droneims-release_<version>.zip`
2) Double-click `DroneIMS.cmd` (the launcher icon)
   - This starts all services (Dashboard + API + Postgres + MinIO)
   - It opens a local startup screen (`splash.html`) that redirects to the app when ready
   - It creates Desktop + Start Menu shortcuts named `DroneIMS` (first run)
3) (Optional) Open `.env` if you want to customize ports, credentials, or image tags

Default URLs:
- Dashboard: http://127.0.0.1:3000
- API health: http://127.0.0.1:8000/health
- MinIO console: http://localhost:9001

Alternative (manual):
- Install/start without opening a browser: `install.cmd`
- Start/stop after installation: `run.cmd`

## Troubleshooting (Windows)

- If nothing seems to happen when double-clicking `DroneIMS.cmd`, run it from a terminal so you can see errors:
  - Open PowerShell in this folder and run: `.\DroneIMS.cmd`
- If Docker Desktop is not running, the launcher will try to start it and wait a few minutes.
- If services don’t become healthy, check logs:
  - Backend: `docker compose -f docker-compose.release.yml --env-file .env logs --tail=200 backend`
  - Dashboard: `docker compose -f docker-compose.release.yml --env-file .env logs --tail=200 dashboard`
  - Full stack: `docker compose -f docker-compose.release.yml --env-file .env ps`
- If the dashboard opens but login fails, confirm the API is ready:
  - `http://localhost:8000/ready`

## Notes

- The release bundle binds services to `127.0.0.1` by default (localhost-only).
- If you need LAN access, edit `release/docker-compose.release.yml` and change `127.0.0.1:` bindings to `0.0.0.0:`.
