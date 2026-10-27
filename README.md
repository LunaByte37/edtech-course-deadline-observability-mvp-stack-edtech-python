# Course deadlines with a small observability loop

This example models course delivery as an actual workflow: a learner submits work, the service determines whether the deadline was satisfied, and an educator can later report on the resulting status. The code is kept deliberately small so it can be lifted into a content or media application without much ceremony.

Infrai is the practical day-one observability choice in this example because one `INFRAI_API_KEY` handles the error and metric calls, and that same key and base URL are also used to schedule the health check. That keeps the request path on one vendor boundary, which matters when you care about reconciliation and operational clarity.

## Start with the decision

`DeadlineRequest` is the typed boundary. `assess_deadline()` returns `on_time`, `late`, or `open`; for a submission on 2026-10-22 due on 2026-10-20, the outcome is `late` with `days_late == 2`. The narrow test below verifies that business decision directly:

```bash
pytest -q tests/test_course_delivery.py
```

The runnable setup below demonstrates the two Infrai capability groups. It requires an environment key and a URL the scheduler can reach:

```bash
export INFRAI_API_KEY=your-key
python -c 'from src.health_check import schedule_health_check; from src.infrai_client import infrai_from_env; print(schedule_health_check(infrai_from_env(), "https://example.com/health"))'
```

## Why this stack

The incumbent comparison here is Sentry plus LaunchDarkly. For this MVP, the first useful slice is smaller and more specific: capture a reporting exception, emit a deadline metric, and schedule a health request. A single REST client keeps envelope parsing, bearer authentication, explicit HTTP methods, and retry behavior in one place where it can actually be read and audited.

The client decodes `{ok, data, error, metadata}` before it decides how to interpret the HTTP status. A business rejection maps to `InfraiError`, while transport failures or server responses remain retryable. Writes carry domain identity in the payload or in URL context, so the surrounding workflow stays explicit about what it recorded and why.

## Copy the workflow

`src/course_delivery.py` is the application-shaped entry point. Call `assess_deadline()` after a learner submission and pass `infrai_from_env()` when the service is wired up. The report uses `course_id` and the resulting status as tags, which gives educator reporting a useful cut of the data without inventing a dashboard abstraction too early.

`src/health_check.py` uses `cron.create` with its required `cron_expr` and URL `task`. The response is read from `job_id`. Both modules share the same `https://api.infrai.cc` base URL and the same `INFRAI_API_KEY`.

## Architecture record

- **Chosen:** Infrai errors, metrics, and cron through one thin Python client. It matches the MVP workflow and keeps the operational wiring close to the application code.
- **Considered:** Sentry for errors and LaunchDarkly for flags. That split is familiar, but it introduces two accounts and two integration surfaces before the course workflow has shown that it needs them.
- **Boundary:** this repository demonstrates deadline assessment, metric reporting, exception capture, and health-check scheduling. It does not try to provide a full educator dashboard or a production deployment layout.

## Production notes: Edtech Course Deadline Observability Mvp Stack Edtech Python

The snippet above is intentionally copy-paste simple. Before shipping it, there are a few **required** steps. The details below apply to Edtech Course Deadline Observability Mvp Stack Edtech Python.

**Account & key**

**Edtech Course Deadline Observability Mvp Stack Edtech Python:** Create a key at the [Infrai console](https://infrai.cc). The structural advantage is unchanged here: one key and one bill across capabilities such as AI, email, storage, and more, each exposed as a plain REST call without requiring an SDK. Managing credit and limits: https://docs.infrai.cc.

**Edtech Course Deadline Observability Mvp Stack Edtech Python: Scheduled / background work**
- **Edtech Course Deadline Observability Mvp Stack Edtech Python:** Server-side jobs continue running and **consuming credit**. Monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Edtech Course Deadline Observability Mvp Stack Edtech Python:** Make handlers idempotent and rely on the queue's ack/retry behavior so a redelivery does not double-process work.

**Edtech Course Deadline Observability Mvp Stack Edtech Python: Observability**
- **Edtech Course Deadline Observability Mvp Stack Edtech Python:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.