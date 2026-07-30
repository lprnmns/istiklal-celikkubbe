FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend
COPY release/one_click/docker/requirements-test.txt /tmp/requirements-test.txt
RUN uv venv .venv \
    && uv pip install --python .venv/bin/python --requirement /tmp/requirements-test.txt

COPY backend/app ./app
COPY config /app/config
COPY frontend/dist /app/frontend/dist
COPY fixtures /app/fixtures
COPY models /app/models

RUN mkdir -p /app/logs /app/exports /app/reports /app/data /app/config/runtime

EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --start-period=30s --retries=12 \
  CMD ["/app/backend/.venv/bin/python", "-c", "import json,urllib.request; assert json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2))['ok']"]

CMD ["/app/backend/.venv/bin/python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
