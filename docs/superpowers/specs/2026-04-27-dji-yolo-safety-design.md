# DJI MSDK Bridge + YOLO Model Registry + Safety Detection + 3D Mapping (DroneIMS Design)

Date: 2026-04-27

## 0) Scope

This document specifies the design for adding:

1) A YOLO “bring your own weights” capability (ONNX-first, optional `.pt`) with a model registry, admin UI, and worker-based inference jobs.
2) Safety mitigation features for warehouses using captured imagery:
   - pallets at higher levels leaning/broken/damaged,
   - smoke channel correctness/obstructions between pallet stacks.
3) DJI Mavic 3 Enterprise integration for “full control” via DJI Mobile SDK (MSDK), implemented as an Android bridge that communicates with the existing DroneIMS backend running on a Windows laptop.
4) A capture-to-digital-twin mapping workflow (M3E capture → COLMAP/Open3D pipeline → mesh upload → 3D viewer/markers).

Non-goals (initially):
- Direct flight control from Windows without an Android bridge.
- Guaranteeing MSDK feature availability on a specific DJI RC device model if the OS is locked down.
- Real-time, low-latency live video streaming in the first implementation (media sync + frame extraction is sufficient).

## 1) Current Repo Context (Key Extension Points)

Existing, stable seams already present in the repo:

- Evidence ingestion and job enqueue:
  - Presign upload → upload artifact to MinIO/S3 → confirm → optional auto-enqueue.
  - This is the primary ingestion path the DJI bridge will use.
- Background worker model:
  - Worker drains jobs from Postgres (no external queue required).
- CV engine structure:
  - Modular pipeline intended for preprocess → region-detect → decode; YOLOv8 wrapper exists but is not yet wired into production scan processing.
- 3D warehouse map viewer + markers:
  - Warehouse maps stored in object storage; marker CRUD tied to map versions.

## 2) Requirements

### 2.1 Functional Requirements

**R1 — Model registry**
- Admin can upload a detection model artifact and register it as a versioned “model” entity.
- Models are stored in S3-compatible storage; metadata is stored in Postgres.
- Admin can activate one model per “task type” (inventory, safety-pallet, safety-smoke, mapping-aid).

**R2 — YOLO inference jobs**
- Operator or system can enqueue inference against an evidence item (image or extracted frame).
- Worker runs inference and stores structured detections and references to any derived artifacts (annotated overlays).

**R3 — Safety workflows**
- System can run a safety inspection job that produces:
  - pallet damage/lean risk findings,
  - smoke channel obstruction findings,
  - severity score and explanation fields,
  - location association (warehouse + optional map marker/location id).
- Dashboard can view results and overlay detections on the original image and/or in the 3D map viewer.

**R4 — DJI MSDK bridge**
- Android app (running on DJI RC / Android) performs:
  - mission execution control (waypoints/capture plan) where allowed by MSDK,
  - telemetry collection,
  - media capture + upload to DroneIMS.
- Bridge can push media/telemetry to the Windows laptop on LAN/Wi‑Fi.

**R5 — 3D mapping pipeline**
- A “3D mapping capture” mission can collect imagery and metadata sufficient to run photogrammetry.
- A server-side pipeline produces a warehouse map asset (mesh/point cloud) and registers a new map version.

### 2.2 Non-Functional Requirements

**NFR1 — Security**
- Default model artifact format is ONNX.
- Any `.pt` ingestion is treated as privileged and must be explicitly enabled/configured (admin-only).
- Uploaded model artifacts are stored with integrity metadata (size/hash).
- Role-based authorization applied to model management and safety runs.

**NFR2 — Self-hostable**
- All new capabilities must run in the current self-hosted Docker-based architecture.

**NFR3 — Auditability**
- Safety results and model version used must be stored and traceable per run.

## 3) High-Level Architecture

### 3.1 Components

1) **DroneIMS API (FastAPI)**
   - Adds endpoints for model registry, safety runs, telemetry ingestion, mission capture sessions.
2) **DroneIMS Worker**
   - Adds job types:
     - `ai_inference_job` (YOLO inference + artifact generation),
     - `safety_inspection_job` (or a thin wrapper around inference + rule aggregation),
     - `mapping_job` (pipeline orchestration).
3) **Object Storage (MinIO/S3)**
   - Stores:
     - model artifacts,
     - captured evidence (images/video),
     - derived artifacts (annotated overlays, frame extracts),
     - mapping outputs (mesh, point cloud).
4) **Dashboard (Next.js)**
   - Admin screens for model upload/activation.
   - Safety results screens with image overlays and map association.
5) **DJI Bridge (Android)**
   - Talks to DJI MSDK locally and DroneIMS API over LAN.

### 3.2 Data Flow

**DJI capture → evidence**
1) Bridge requests presigned PUT from DroneIMS.
2) Bridge uploads media file to MinIO/S3.
3) Bridge calls confirm endpoint with metadata (mission_id, drone_id, capture timestamp, optional pose/telemetry ref).
4) DroneIMS optionally enqueues inference/safety jobs based on mission type and configuration.

**Inference → results**
1) Worker downloads evidence object.
2) Worker runs detection using the active model for the requested task type.
3) Worker stores detections + annotated overlay artifact in object storage.
4) Dashboard retrieves detections and overlay URLs via API.

**Mapping → warehouse map**
1) Worker collects capture set from storage.
2) Worker executes photogrammetry pipeline (COLMAP/Open3D tooling).
3) Worker uploads final mesh/point cloud and creates a new warehouse map version.
4) Dashboard updates viewer to show the new map version and related markers/findings.

## 4) Data Model (Proposed)

### 4.1 AI Models

**ai_models**
- id (uuid)
- name (string)
- task_type (enum): `inventory`, `safety_pallet`, `safety_smoke`, `mapping`
- format (enum): `onnx`, `pt`
- artifact_key (string) – object storage path
- artifact_sha256 (string)
- artifact_size_bytes (int)
- classes_json (json) – label set and any id mapping
- is_active (bool)
- created_by_user_id (uuid)
- created_at (timestamp)

### 4.2 Inference Runs

**ai_inference_runs**
- id (uuid)
- warehouse_id (uuid)
- mission_id (uuid, nullable)
- evidence_object_key (string)
- model_id (uuid)
- task_type (enum)
- status (enum): `queued`, `running`, `succeeded`, `failed`
- started_at / finished_at
- error_message (string, nullable)
- overlay_object_key (string, nullable)

**ai_detections**
- id (uuid)
- run_id (uuid)
- class_name (string)
- confidence (float)
- bbox_json (json) – x/y/w/h (and optionally normalized coords)
- attributes_json (json) – task-specific attributes (e.g., “lean_score”, “damage_type”)

### 4.3 Telemetry (Minimal First)

**drone_sessions**
- id (uuid)
- drone_id (string) – e.g., “dji-m3e-001”
- mission_id (uuid)
- started_at / ended_at
- source (string) – “dji_msdk_bridge”

**drone_telemetry_points**
- id (uuid)
- session_id (uuid)
- ts (timestamp)
- lat/lon/alt (float nullable)
- yaw/pitch/roll (float nullable)
- extras_json (json) – optional expansion

### 4.4 Safety Findings

**safety_findings**
- id (uuid)
- warehouse_id (uuid)
- mission_id (uuid, nullable)
- run_id (uuid) – inference run used
- category (enum): `pallet_damage`, `pallet_lean`, `smoke_channel_obstruction`
- severity (enum/int)
- description (string)
- marker_id (uuid, nullable) – association to map marker/location when available
- created_at

## 5) API Surface (Proposed)

### 5.1 Model Registry (Admin)
- `POST /api/v1/ai/models/presign` – presign model upload
- `POST /api/v1/ai/models/confirm` – register model metadata + artifact key/hash
- `GET /api/v1/ai/models` – list models
- `POST /api/v1/ai/models/{id}/activate` – activate model for its task type

### 5.2 Inference + Safety
- `POST /api/v1/ai/inference` – enqueue inference on a given evidence object key / scan result
- `GET /api/v1/ai/inference/{id}` – get run status + detections + overlay URL
- `POST /api/v1/safety/inspect` – enqueue safety inspection (wraps inference + finding aggregation)
- `GET /api/v1/safety/findings` – list findings (filters: warehouse, mission, severity, category)

### 5.3 Telemetry Ingestion (From DJI Bridge)
- `POST /api/v1/drone/sessions` – create session
- `POST /api/v1/drone/sessions/{id}/telemetry` – push telemetry batch

## 6) Dashboard UX (Proposed)

### 6.1 Admin: Models
- Upload model (format selection; ONNX default)
- Set task type
- Activate model per task type

### 6.2 Operations: Safety
- Safety findings list with filtering (warehouse/mission/severity/category)
- Evidence viewer:
  - show original image/video frame
  - overlay detections
  - link to 3D map marker/location if available

## 7) DJI MSDK Bridge (Android) Design

### 7.1 Responsibilities
- Authenticate to DroneIMS (device/service credentials).
- Obtain presigned URLs and upload media.
- Create/attach evidence to missions and sessions.
- Stream telemetry as batches.
- Execute mission control where permitted by DJI MSDK.

### 7.2 Connectivity to Laptop
- Bridge pushes data to `http://<laptop-ip>:8000` over Wi‑Fi/LAN.
- If the laptop is localhost-only by default, provide a documented option to enable LAN binding for the API in the release compose file.

### 7.3 Fallback Behavior
- If “full control” APIs are unavailable on the controller device, bridge still supports:
  - media upload + confirm,
  - telemetry upload (when accessible),
  - marking capture sets for mapping jobs.

## 8) Security Notes

- ONNX-first model ingestion reduces the risk associated with untrusted `.pt` weights.
- `.pt` model ingestion must be gated behind admin authorization and an explicit configuration flag.
- Store `sha256` and `size_bytes` for model artifacts and verify on download before inference.

## 9) Testing Strategy

- Unit tests:
  - model registry validation
  - inference job state transitions
  - safety finding aggregation logic
- Integration tests:
  - presign → upload → confirm for model artifacts
  - enqueue inference → worker executes → results returned
- Contract tests for DJI bridge endpoints:
  - telemetry batch ingestion
  - evidence upload metadata correctness

## 10) Rollout Plan (High Level)

1) Model registry + ONNX ingestion.
2) Inference jobs + dashboard overlays.
3) Safety findings aggregation and UI.
4) DJI bridge ingestion endpoints + mission/session plumbing.
5) Mapping job orchestration integration with capture sets.
