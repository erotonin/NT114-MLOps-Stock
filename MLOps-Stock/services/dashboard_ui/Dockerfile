# syntax=docker/dockerfile:1.4
# ============================================================
# Dashboard UI — Chỉ phục vụ giao diện web, siêu nhẹ
# ============================================================
FROM python:3.11.15-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Layer 1: Dependencies (cached mạnh — chỉ rebuild khi requirements thay đổi)
COPY services/dashboard_ui/requirements.txt .
RUN pip install --no-cache-dir --timeout 300 --retries 10 -r requirements.txt

# Layer 2: Source code (thay đổi thường xuyên — rebuild nhanh)
COPY services/dashboard_ui/ /app/

# Security: Non-root user
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8081
CMD ["uvicorn", "main_web:app", "--host", "0.0.0.0", "--port", "8081"]
