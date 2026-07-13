FROM python:3.11-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV UV_SYSTEM_PYTHON=1
ENV UV_HTTP_TIMEOUT=120

RUN set -eux; \
    echo "backend build: switching Debian package sources to HTTPS"; \
    sed -i 's|URIs: http://deb.debian.org|URIs: https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources; \
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

COPY requirements.txt ./
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

ENV PYTHONPATH=/app

CMD ["python", "-m", "app.main"]

FROM base AS runtime
