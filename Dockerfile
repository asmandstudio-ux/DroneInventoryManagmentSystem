FROM python:3.12-slim AS base

WORKDIR /srv/app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# OpenCV (opencv-python-headless) runtime deps on Debian slim.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      libglib2.0-0 \
      libgl1 \
      libzbar0 \
      ca-certificates \
      curl \
      tini \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic

# Drop root privileges in runtime containers.
RUN useradd --create-home --home-dir /home/appuser --shell /usr/sbin/nologin --uid 10001 appuser \
    && chown -R appuser:appuser /srv/app

FROM base AS api
EXPOSE 8000
USER appuser
ENTRYPOINT ["tini", "--"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS worker
USER appuser
ENTRYPOINT ["tini", "--"]
CMD ["python", "-m", "app.worker"]

# Test runner image (includes pytest + httpx + pytest-asyncio).
# Use via docker compose profile "test" (see docker-compose.yml).
FROM base AS test
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY tests ./tests
USER appuser
ENTRYPOINT ["tini", "--"]
CMD ["pytest", "-q"]

