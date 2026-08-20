# syntax=docker/dockerfile:1.4
# ============================================================
# Ensemble API — Gateway gom kết quả từ TFT + LGBM, tải meta-learner từ MLflow
# ============================================================
FROM python:3.11.15-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"

# Defaults cho in-cluster communication
ENV MLFLOW_TRACKING_URI="http://mlflow-svc.mlops-infra.svc.cluster.local:5000"

WORKDIR /app

# Layer 1: Dependencies (cached — không cần torch hay lightgbm)
COPY services/ensemble_api/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Layer 2: Shared source modules
COPY src/ /app/src/

# Layer 3: Service code
COPY services/ensemble_api/ /app/

# Security: Non-root user
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
