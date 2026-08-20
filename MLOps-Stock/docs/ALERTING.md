# Alerting

## Design

Monitor API emits an alert whenever the drift policy returns `alert` or `retrain`. In local-offline mode, the event is appended to `artifacts/alerts.jsonl`, which makes the behavior deterministic and demonstrable without external credentials. If `ALERT_WEBHOOK_URL` is configured, the same JSON payload is sent with a five-second timeout; webhook failures are recorded in the payload and never stop monitoring.

The readiness endpoint is `GET http://127.0.0.1:8084/alerts/health`. The current Compose acceptance response is HTTP 200 with `mode=local_jsonl`. Prometheus metrics remain available at `/metrics`.

## Payload

```json
{
  "timestamp": "UTC ISO-8601 timestamp",
  "ticker": "FPT",
  "severity": "critical",
  "action": "retrain",
  "reason": "policy reason",
  "source": "monitor-api",
  "details": "drift summary, performance and policy metadata"
}
```

## Configuration

| Environment variable | Default | Purpose |
|---|---|---|
| `ALERT_LOG_PATH` | `artifacts/alerts.jsonl` | Local append-only JSONL sink |
| `ALERT_WEBHOOK_URL` | unset | Optional Slack/Telegram/internal webhook endpoint |

The alert sink has a dedicated unit test. The current host regression suite completes with **29 passed**. The implementation intentionally does not embed credentials or make outbound requests unless the webhook variable is explicitly configured.
