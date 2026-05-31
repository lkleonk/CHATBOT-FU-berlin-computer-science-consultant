FROM python:3.11-slim-bookworm

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

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    set -eux; \
    echo "backend build: installing uv package manager"; \
    pip install --prefer-binary uv; \
    echo "backend build: uv installed"

RUN --mount=type=cache,target=/root/.cache/uv \
    set -eux; \
    echo "backend build: installing CPU PyTorch from PyTorch wheel index"; \
    uv pip install --system --extra-index-url https://download.pytorch.org/whl/cpu "torch==2.5.1+cpu"; \
    echo "backend build: installing backend Python requirements"; \
    uv pip install --system -r requirements.txt; \
    echo "backend build: Python dependencies installed"

COPY app ./app
COPY scripts ./scripts
COPY knowledge_base ./knowledge_base

ENV PYTHONPATH=/app

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5100"]
