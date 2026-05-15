from __future__ import annotations

import uuid

import pytest


async def _register_and_login(client, *, email: str, password: str, role: str) -> str:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User", "role": role},
    )
    assert reg.status_code in (201, 400), reg.text

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


@pytest.mark.asyncio
async def test_presign_confirm_and_process_flow(client, monkeypatch):
    from app.core.config import settings
    from app.services.s3_service import S3Service

    monkeypatch.setattr(S3Service, "presign_put_url", lambda self, *, object_key, content_type, expires_in=None: "http://s3/presigned-put")
    monkeypatch.setattr(
        S3Service,
        "head_object",
        lambda self, *, object_key: {"etag": "etag123", "bytes": 123, "content_type": "image/jpeg"},
    )

    prev_inline = settings.SCAN_JOBS_INLINE
    settings.SCAN_JOBS_INLINE = False

    try:
        email = f"op-{uuid.uuid4()}@example.com"
        sup_email = f"sup-{uuid.uuid4()}@example.com"
        password = "passw0rd-123"

        op_token = await _register_and_login(client, email=email, password=password, role="operator")
        sup_token = await _register_and_login(client, email=sup_email, password=password, role="supervisor")

        op_headers = {"Authorization": f"Bearer {op_token}"}
        sup_headers = {"Authorization": f"Bearer {sup_token}"}

        mission = await client.post(
            "/api/v1/missions",
            json={"title": "M1", "description": "d", "priority": 1, "drone_id": "dji-m3e", "waypoints": {}},
            headers=op_headers,
        )
        assert mission.status_code == 201, mission.text
        mission_id = mission.json()["id"]

        scan = await client.post(
            "/api/v1/scan-results",
            json={"mission_id": mission_id, "drone_id": "dji-m3e", "data": {}},
            headers=op_headers,
        )
        assert scan.status_code == 201, scan.text
        scan_id = scan.json()["id"]

        presign = await client.post(
            "/api/v1/uploads/presign",
            json={"scan_result_id": scan_id, "content_type": "image/jpeg", "filename": "img.jpg"},
            headers=op_headers,
        )
        assert presign.status_code == 200, presign.text
        body = presign.json()
        assert body["method"] == "PUT"
        assert body["url"] == "http://s3/presigned-put"
        assert body["headers"]["Content-Type"] == "image/jpeg"
        assert body["object_key"].startswith(f"evidence/scan-results/{scan_id}/")

        confirm = await client.post(
            "/api/v1/uploads/confirm",
            json={"scan_result_id": scan_id, "etag": "etag123", "bytes": 123},
            headers=op_headers,
        )
        assert confirm.status_code == 200, confirm.text
        conf = confirm.json()
        assert conf["scan_result_id"] == scan_id
        assert conf["object_key"] == body["object_key"]
        assert conf["etag"] == "etag123"
        assert conf["bytes"] == 123
        assert conf["uploaded_at"]
        assert conf["scan_job_id"]

        job = await client.get(f"/api/v1/scan-jobs/{conf['scan_job_id']}", headers=sup_headers)
        assert job.status_code == 200, job.text
        assert job.json()["scan_result_id"] == scan_id

        process = await client.post(f"/api/v1/scan-results/{scan_id}/process", json={}, headers=op_headers)
        assert process.status_code == 202, process.text
        assert process.json()["scan_result_id"] == scan_id
    finally:
        settings.SCAN_JOBS_INLINE = prev_inline


@pytest.mark.asyncio
async def test_uploads_confirm_enforces_owner_access(client, monkeypatch):
    from app.core.config import settings
    from app.services.s3_service import S3Service

    monkeypatch.setattr(S3Service, "presign_put_url", lambda self, *, object_key, content_type, expires_in=None: "http://s3/presigned-put")
    monkeypatch.setattr(
        S3Service,
        "head_object",
        lambda self, *, object_key: {"etag": "etag123", "bytes": 123, "content_type": "image/jpeg"},
    )

    prev_inline = settings.SCAN_JOBS_INLINE
    settings.SCAN_JOBS_INLINE = False

    try:
        password = "passw0rd-123"
        owner_email = f"owner-{uuid.uuid4()}@example.com"
        other_email = f"other-{uuid.uuid4()}@example.com"

        owner_token = await _register_and_login(client, email=owner_email, password=password, role="operator")
        other_token = await _register_and_login(client, email=other_email, password=password, role="operator")

        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        other_headers = {"Authorization": f"Bearer {other_token}"}

        mission = await client.post(
            "/api/v1/missions",
            json={"title": "M2", "description": "d", "priority": 1, "drone_id": "dji-m3e", "waypoints": {}},
            headers=owner_headers,
        )
        assert mission.status_code == 201, mission.text
        mission_id = mission.json()["id"]

        scan = await client.post(
            "/api/v1/scan-results",
            json={"mission_id": mission_id, "drone_id": "dji-m3e", "data": {}},
            headers=owner_headers,
        )
        assert scan.status_code == 201, scan.text
        scan_id = scan.json()["id"]

        presign = await client.post(
            "/api/v1/uploads/presign",
            json={"scan_result_id": scan_id, "content_type": "image/jpeg", "filename": "img.jpg"},
            headers=owner_headers,
        )
        assert presign.status_code == 200, presign.text

        confirm_other = await client.post(
            "/api/v1/uploads/confirm",
            json={"scan_result_id": scan_id, "etag": "etag123", "bytes": 123},
            headers=other_headers,
        )
        assert confirm_other.status_code == 403
    finally:
        settings.SCAN_JOBS_INLINE = prev_inline


@pytest.mark.asyncio
async def test_scan_jobs_object_level_access(client):
    password = "passw0rd-123"
    owner_email = f"owner-{uuid.uuid4()}@example.com"
    other_email = f"other-{uuid.uuid4()}@example.com"
    sup_email = f"sup-{uuid.uuid4()}@example.com"

    owner_token = await _register_and_login(client, email=owner_email, password=password, role="operator")
    other_token = await _register_and_login(client, email=other_email, password=password, role="operator")
    sup_token = await _register_and_login(client, email=sup_email, password=password, role="supervisor")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}
    sup_headers = {"Authorization": f"Bearer {sup_token}"}

    mission = await client.post(
        "/api/v1/missions",
        json={"title": "M3", "description": "d", "priority": 1, "drone_id": "dji-m3e", "waypoints": {}},
        headers=owner_headers,
    )
    assert mission.status_code == 201, mission.text
    mission_id = mission.json()["id"]

    scan = await client.post(
        "/api/v1/scan-results",
        json={"mission_id": mission_id, "drone_id": "dji-m3e", "data": {}},
        headers=owner_headers,
    )
    assert scan.status_code == 201, scan.text
    scan_id = scan.json()["id"]

    job = await client.post(f"/api/v1/scan-results/{scan_id}/process", json={}, headers=owner_headers)
    assert job.status_code == 202, job.text
    job_id = job.json()["id"]

    get_owner = await client.get(f"/api/v1/scan-jobs/{job_id}", headers=owner_headers)
    assert get_owner.status_code == 200, get_owner.text
    assert get_owner.json()["scan_result_id"] == scan_id

    get_other = await client.get(f"/api/v1/scan-jobs/{job_id}", headers=other_headers)
    assert get_other.status_code == 403

    get_sup = await client.get(f"/api/v1/scan-jobs/{job_id}", headers=sup_headers)
    assert get_sup.status_code == 200, get_sup.text

    list_owner = await client.get("/api/v1/scan-jobs?limit=100&offset=0", headers=owner_headers)
    assert list_owner.status_code == 200, list_owner.text
    assert any(j["id"] == job_id for j in list_owner.json())

    list_sup = await client.get("/api/v1/scan-jobs?limit=100&offset=0", headers=sup_headers)
    assert list_sup.status_code == 200, list_sup.text
    assert any(j["id"] == job_id for j in list_sup.json())

    enqueue_owner = await client.post("/api/v1/scan-jobs", json={"scan_result_id": scan_id}, headers=owner_headers)
    assert enqueue_owner.status_code == 202, enqueue_owner.text
    assert enqueue_owner.json()["id"] == job_id

    enqueue_other = await client.post("/api/v1/scan-jobs", json={"scan_result_id": scan_id}, headers=other_headers)
    assert enqueue_other.status_code == 403
