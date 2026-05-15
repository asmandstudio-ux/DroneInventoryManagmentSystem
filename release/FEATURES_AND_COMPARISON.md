# DroneIMS (Drone Inventory Management System)
## Feature Overview & Comparison

This document describes what DroneIMS does, how it’s structured, and how it compares to similar warehouse inventory automation solutions.

## What DroneIMS Is

DroneIMS is a self-hostable warehouse inventory management platform that combines:
- A web dashboard for operators
- A FastAPI backend for APIs and business logic
- Postgres for system-of-record data
- S3-compatible object storage (MinIO in the standalone bundle) for evidence/attachments and warehouse map artifacts
- A 3D warehouse map viewer for interactive visualization and marker management

It is designed to be deployable as a standalone bundle using Docker Desktop on Windows.

## Core Features

### Users, Authentication, and Access Control
- User accounts with role-based access control (RBAC)
- API endpoints protected by role checks for sensitive operations

### Warehouses and Inventory Locations
- Warehouse management primitives (warehouses, locations, and related operational entities)
- Warehouse-specific assets (such as 3D map mesh + markers)

### Missions and Job Execution
- Create/manage scan or mission-like tasks
- Background-worker support for long-running processing

### Scan Results and Evidence
- Store scan outcomes and attach evidence (images/files) to results
- S3/MinIO-backed file storage with server-side verification

### Reports
- Operational reporting endpoints and UI surfaces (inventory/scan-related reporting)

### 3D Warehouse Map and Interactive Markers
- Upload a warehouse mesh (GLB/GLTF; PLY/OBJ via octet-stream)
- Generate presigned upload URLs for large artifacts
- 3D viewer with:
  - Click/select markers
  - Add markers via 3D interaction
  - Edit marker metadata (label/type/notes)
  - Persist markers as structured data tied to a warehouse map version

### Storage Model
- Structured data: Postgres
- Binary artifacts: S3-compatible object storage (MinIO in the release bundle)
- Presigned upload/download to avoid proxying large files through the backend

## Deployment/Operations (Standalone Bundle)

The `release/` folder ships:
- `install.cmd` / `install.ps1`: sets up `.env`, optionally loads offline images, starts the stack
- `run.cmd` / `run.ps1`: start/stop convenience wrappers
- `docker-compose.release.yml`: Postgres + MinIO + backend + dashboard (plus health checks)
- Optional offline tarballs under `release/images/`

Default URLs:
- Dashboard: http://localhost:3000
- API: http://localhost:8000
- MinIO console: http://localhost:9001

## Comparison to Similar Software

DroneIMS is primarily a software platform you host and customize. Many “warehouse inventory automation” products are bundled with proprietary robotics hardware and managed service delivery.

### Summary Matrix (High-Level)

| Capability | DroneIMS (this repo) | Verity | Gather AI | Dexory |
|---|---|---|---|---|
| Self-hostable (on-prem) | Yes (Docker Compose bundle) | Typically vendor-managed | Typically vendor-managed | Typically vendor-managed |
| Includes proprietary robots/drones | No (platform/software) | Yes (autonomous indoor drones + system) | Uses off-the-shelf drones + vendor stack | Yes (autonomous robots + system) |
| Primary data capture | Depends on integrator | Autonomous indoor drones scanning inventory | Autonomous drone flights capturing images + CV | Autonomous robots capturing visual/3D data |
| Digital twin / 3D facility model | 3D map viewer + markers | AI-enabled digital twin positioning | “Digitized warehouse” style search/visibility | Live digital twin emphasized |
| Inventory exception workflows | Yes (scan results + evidence + reporting) | Dashboard insights + WMS integration | Exception reports + workflow automation | Real-time discrepancy flagging + analytics |
| Integration with WMS | API-first (customizable) | Integrates into WMS (vendor claim) | Integrates with WMS/ERP (vendor claim) | Integrates with major WMS (vendor claim) |
| Deployment time | Depends on your infra/process | Vendor claims fast deployment | Vendor claims rapid “plug-and-play” | Vendor claims rapid deployment |

### Notes on Each Vendor (From Public Sources)

- Verity positions itself around fully autonomous indoor drones, “smart scanning” (cycle counts, empty bin scans, moved location checks) and an AI-powered digital twin feeding insights to a dashboard/WMS. [1]
- Gather AI emphasizes a software-first approach using drones + computer vision to generate exception reports and automate workflows; their own description highlights plug-and-play deployment and inventory intelligence. [2]
- Dexory emphasizes autonomous robots scanning sites to build a live digital twin with AI-driven insights and real-time discrepancy flagging. [3]

### Where DroneIMS Fits Best

DroneIMS is a better fit when you want:
- A self-hosted, customizable platform you can extend
- Full control over data residency and integrations
- A 3D warehouse map UI tailored to your operation (custom marker schemas, workflows, and permissions)

Vendor systems (Verity/Gather AI/Dexory) are a better fit when you want:
- Turnkey robotics + maintenance + support bundled into the solution
- SLA-backed scanning operations and hardware lifecycle handled externally

## Sources

1. Verity – solution overview: https://www.verity.net/solution/
2. Gather AI – AI-powered drones overview: https://www.gather.ai/ai-powered-drones
3. Dexory – inventory automation & warehouse optimisation overview: https://www.dexory.com/

