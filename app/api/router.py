from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import auth, missions, reports, risk_events, scan_jobs, scan_results, uploads, warehouses, warehouse_maps

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(missions.router, prefix="/missions", tags=["missions"])
api_router.include_router(scan_results.router, prefix="/scan-results", tags=["scan-results"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(warehouses.router, prefix="/warehouses", tags=["warehouses"])
api_router.include_router(warehouse_maps.router, prefix="/warehouses", tags=["warehouse-maps"])
api_router.include_router(risk_events.router, prefix="/risk-events", tags=["risk-events"])
api_router.include_router(scan_jobs.router, prefix="/scan-jobs", tags=["scan-jobs"])

