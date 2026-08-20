# syntax=docker/dockerfile:1.4
# ============================================================
# Monitor API — Drift Detection bằng Evidently AI + Prometheus Metrics
# ============================================================
FROM python:3.11.15-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"

WORKDIR /app

# Layer 1: Python Dependencies
COPY services/monitor_api/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Layer 2: Shared source modules
COPY src/ /app/src/

# Layer 3: Service code
COPY services/monitor_api/ /app/

# Security: Non-root user
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8084
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8084"]
