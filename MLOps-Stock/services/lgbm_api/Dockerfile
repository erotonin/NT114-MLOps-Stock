# syntax=docker/dockerfile:1.4
# ============================================================
# LightGBM API — Dự đoán bằng GBDT, tải weights từ MLflow/MinIO
# ============================================================
FROM python:3.11.15-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"

# Defaults cho in-cluster communication (override bằng K8s env khi deploy)
ENV MLFLOW_TRACKING_URI="http://mlflow-svc.mlops-infra.svc.cluster.local:5000"

WORKDIR /app

# Layer 1: System dependencies for LightGBM
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

# Layer 2: Python Dependencies (cached — lightgbm nhẹ hơn torch rất nhiều)
COPY services/lgbm_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Layer 2: Shared source modules
COPY src/ /app/src/

# Layer 3: Service code
COPY services/lgbm_api/ /app/

# Security: Non-root user
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8003
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
