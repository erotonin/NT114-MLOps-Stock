# syntax=docker/dockerfile:1.4
# ============================================================
# TFT API — Dự đoán bằng Neural Network (PyTorch CPU-only)
# ============================================================
FROM python:3.11.15-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"

# Defaults cho in-cluster communication
ENV MLFLOW_TRACKING_URI="http://mlflow-svc.mlops-infra.svc.cluster.local:5000"

WORKDIR /app

# Layer 1: Dependencies (cached — dùng torch CPU-only, nhẹ hơn ~1.5GB so với bản đầy đủ)
COPY services/tft_api/requirements.txt .
RUN pip install --no-cache-dir --timeout 300 --retries 10 -r requirements.txt

# Layer 2: Shared source modules
COPY src/ /app/src/

# Layer 3: Service code
COPY services/tft_api/ /app/

# Security: Non-root user
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8002
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
