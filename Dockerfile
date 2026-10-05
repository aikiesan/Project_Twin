FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git poppler-utils libgdal-dev gdal-bin curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# The venv lives outside /work, so bind-mounting the repository (and its host .venv) over /work
# does not hide it.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv UV_LINK_MODE=copy
WORKDIR /work
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --python 3.11 --extra dev --extra nb --extra geo --extra stats --extra db \
    || uv sync --extra dev
