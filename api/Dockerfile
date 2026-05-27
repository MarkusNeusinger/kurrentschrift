# Dockerfile for kurrentschrift FastAPI backend on Cloud Run.
# Pattern mirrors ~/projects/anyplot/api/Dockerfile so deployment scripts
# can be templated identically. Placeholder for v1 — not exercised locally.
FROM python:3.13-slim

WORKDIR /app

# System deps for scipy/skimage wheels + the curl probe.
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy lock/manifest first for layer-caching.
COPY pyproject.toml uv.lock README.md ./

# uv with --frozen so we don't re-resolve from pyproject.toml at build time
# (avoids architecture-specific wheel surprises seen on Cloud Build).
RUN pip install --no-cache-dir uv && \
    uv venv && \
    uv sync --frozen

# Application code. The compute layer lives in /core, the HTTP layer in /api.
COPY api/ ./api/
COPY core/ ./core/
# Loth chart is read by the pipeline; ship it in the image.
COPY data/sources/loth-1866/chart.jpg ./data/sources/loth-1866/chart.jpg

# Non-root user.
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app/.venv/bin
USER appuser

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# Cloud Run injects PORT — bind 0.0.0.0:8000 (Cloud Run rewrites internally).
CMD [".venv/bin/uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
