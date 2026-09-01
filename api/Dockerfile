# Multi-stage Dockerfile for the kurrentschrift FastAPI backend on Cloud Run.
#
# Same shape as app/Dockerfile: a builder stage that installs, and a clean
# runtime stage that only receives the finished artefacts. Measured in Cloud
# Build with the same tool for both, the single-stage version this replaces was
# 1.61 GB unpacked against 531 MB here; in Artifact Registry, which bills the
# compressed layers, it was 584.8 MB. Two layers carried the difference, each
# with a named cause — see the comments at the apt and the COPY --chown lines
# below. Sizes further down are labelled where they are quoted: layer figures
# from `docker history` are unpacked, registry figures are compressed.
#
# Both stages MUST use the same base image: `uv venv` records the interpreter
# path in .venv/pyvenv.cfg and writes /app/.venv/bin shebangs, so the runtime
# stage has to offer the same interpreter at the same path (hence WORKDIR /app
# on both sides too).

FROM python:3.13-slim AS builder

WORKDIR /app

# No build-essential: every one of the 88 packages in uv.lock ships a wheel, so
# nothing is ever compiled here — the toolchain only ever sat there. If a future
# dependency arrives sdist-only, the build fails loudly at this step, which is
# the right place to notice, not a silently fat image.
RUN pip install --no-cache-dir uv

# Lock/manifest first for layer caching. The root project is a virtual one
# (uv.lock: `source = { virtual = "." }`), so this installs dependencies and
# never the project itself — which is why the source tree is not needed yet.
# `--frozen` honors uv.lock instead of re-resolving from pyproject.toml
# (avoids architecture-specific wheel surprises seen on Cloud Build).
COPY pyproject.toml uv.lock README.md ./
RUN uv venv && uv sync --frozen


FROM python:3.13-slim

WORKDIR /app

# curl serves the HEALTHCHECK below, and nothing else needs a system package.
# libgl1 used to be installed here for OpenCV — which this project deliberately
# does not depend on (see tools/eigenhand/fiducial.py), and cv2 appears nowhere
# but in the line that installed the library for it. Together with
# build-essential this apt layer was 638 MB unpacked; it is 13.7 MB now.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser

# `COPY --chown` sets ownership as the layer is written. The old
# `RUN chown -R appuser:appuser /app` did it afterwards, which rewrites every
# touched file into a fresh layer and so duplicated the entire venv — 150.9 MB
# compressed, the second-largest layer in the old image, for a permission bit.
# The venv's executables keep their modes across COPY,
# so the `chmod -R 755 .venv/bin` that used to ride along is gone too.
COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv

# Application code. The compute layer lives in /core, the HTTP layer in /api.
COPY --chown=appuser:appuser api/ ./api/
COPY --chown=appuser:appuser core/ ./core/
# pyproject.toml is a RUNTIME file here, not just a build input: the project is
# a virtual uv workspace rather than an installed distribution, so
# importlib.metadata has no record of it and api.main::_project_version() reads
# this file next to api/ as its one version source. The single-stage build
# shipped it as a side effect of the install step; the runtime stage has to
# receive it on purpose, or every start logs a packaging error and /docs reports
# 0.0.0. A few KB. (The sibling repo anyplot needs no equivalent — its
# api/version.py reads importlib.metadata, which the copied venv carries.)
COPY --chown=appuser:appuser pyproject.toml ./
# Source charts are read by the pipeline; ship the whole tree (~6 MB) so a
# CONFIG.sourceId flip never deploys an image missing its chart.
COPY --chown=appuser:appuser data/sources/ ./data/sources/
# Alembic migrations — shipped so the same image can run `alembic upgrade head`
# as the pre-deploy migrate Cloud Run Job (see api/cloudbuild.yaml).
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser alembic/ ./alembic/
# Seed data the quiz_words migrations (0010/0011) read at apply time — without
# it the migrate job dies on FileNotFoundError (seen on the 0011 deploy).
COPY --chown=appuser:appuser tools/quizgen/quiz_words.json ./tools/quizgen/quiz_words.json
# The crawler pages (app/src/lib/seo/prerender.ts renders them at the APP
# build; the files are committed). `/seo-proxy/{route}` serves them to the
# mapped crawler UAs the site's nginx proxies here — same relative path as in
# a checkout, so core.config's default `prerender_dir` needs no override.
COPY --chown=appuser:appuser app/prerender/ ./app/prerender/

USER appuser

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# Cloud Run injects PORT — bind 0.0.0.0:8000 (Cloud Run rewrites internally).
CMD [".venv/bin/uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
