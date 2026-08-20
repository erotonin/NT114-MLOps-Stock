# syntax=docker/dockerfile:1.4
# ============================================================
# Data API — Kéo dữ liệu chứng khoán từ Yahoo Finance
# ============================================================
FROM python:3.11.15-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"

WORKDIR /app

# Layer 1: Dependencies (cached)
COPY services/data_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Layer 2: Shared source modules
COPY src/ /app/src/

# Layer 3: Service code
COPY services/data_api/ /app/

# Security: Non-root user
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
