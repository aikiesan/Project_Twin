FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git poppler-utils libgdal-dev gdal-bin curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /work
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv sync --extra dev --extra nb --extra geo --extra stats || uv sync --extra dev
