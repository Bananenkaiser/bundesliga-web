# syntax=docker/dockerfile:1
# Multi-arch: baut auch auf Raspberry Pi (arm64, 64-bit Raspberry Pi OS).
FROM python:3.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH=/opt/venv/bin:$PATH

WORKDIR /app

# 1) Nur Abhängigkeiten (Layer bleibt gecacht, solange pyproject/uv.lock gleich).
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=README.md,target=README.md \
    uv sync --frozen --no-dev --no-install-project --no-editable

# 2) App-Code.
COPY pyproject.toml uv.lock README.md ./
COPY app ./app
COPY templates ./templates
COPY static ./static
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

ENV DATA_DIR=/data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
