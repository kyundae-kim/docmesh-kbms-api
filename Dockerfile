# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* /app/
RUN uv sync --no-dev --no-install-project

COPY app /app/app

FROM python:3.11-slim AS runtime

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder --chown=10001:10001 /app/.venv /app/.venv
COPY --from=builder --chown=10001:10001 /app/app /app/app

RUN mkdir -p /app/data && chown -R 10001:10001 /app/data

USER 10001:10001


EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; response = urllib.request.urlopen(\"http://127.0.0.1:8000/health\", timeout=3); status = response.status; response.close(); sys.exit(0 if status == 200 else 1)"]

CMD ["python", "-m", "fastapi", "run", "app/main.py", "--host", "0.0.0.0"]