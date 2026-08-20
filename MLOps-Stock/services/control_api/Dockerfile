FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN useradd --create-home --uid 10001 appuser
COPY services/control_api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY src /app/src
COPY services/control_api /app/services/control_api
RUN mkdir -p /app/artifacts /app/models /app/data && chown -R appuser:appuser /app
USER appuser
EXPOSE 8085
CMD ["uvicorn", "services.control_api.main:app", "--host", "0.0.0.0", "--port", "8085"]
