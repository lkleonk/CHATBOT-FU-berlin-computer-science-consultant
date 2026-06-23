FROM python:3.11-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV UV_SYSTEM_PYTHON=1
ENV UV_HTTP_TIMEOUT=120

RUN set -eux; \
    echo "backend build: updating apt package index using IPv4"; \
    timeout 300s apt-get -o Acquire::ForceIPv4=true update; \
    echo "backend build: installing system build dependencies"; \
    timeout 600s apt-get -o Acquire::ForceIPv4=true install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev; \
    rm -rf /var/lib/apt/lists/*; \
    echo "backend build: system dependencies installed"

WORKDIR /app

COPY requirements.txt requirements-legacy-rag.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    set -eux; \
    echo "backend build: installing uv package manager"; \
    pip install --prefer-binary uv; \
    echo "backend build: uv installed"

RUN --mount=type=cache,target=/root/.cache/uv \
    set -eux; \
    echo "backend build: installing runtime Python requirements"; \
    uv pip install --system -r requirements.txt; \
    echo "backend build: runtime Python dependencies installed"

COPY app ./app
COPY scripts ./scripts
COPY knowledge_base ./knowledge_base

ENV PYTHONPATH=/app

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5100"]

# Built only by the optional legacy-rag Compose service. The normal backend
# target above intentionally does not contain Torch, SentenceTransformer, or
# Qdrant dependencies.
FROM base AS legacy-rag

RUN --mount=type=cache,target=/root/.cache/uv \
    set -eux; \
    echo "legacy-rag build: installing optional ingestion requirements"; \
    uv pip install --system -r requirements-legacy-rag.txt; \
    echo "legacy-rag build: optional ingestion dependencies installed"

FROM base AS runtime
