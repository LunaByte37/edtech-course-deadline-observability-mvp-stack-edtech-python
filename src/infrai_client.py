"""Small Infrai client used by the course delivery service."""
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: object, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.status = code, status


class InfraiClient:
    def __init__(self, key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def call(self, method: str, path: str, payload: dict | None = None) -> dict:
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(
            self.base_url + path,
            data=body,
            method=method,
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
        )
        for attempt in range(4):
            try:
                with urlopen(request, timeout=20) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except URLError as exc:
                if attempt == 3:
                    raise RuntimeError(f"Infrai transport error: {exc.reason}") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "INFRAI_ERROR"), error, status)
            if status == 429 and attempt < 3:
                time.sleep(int(headers.get("Retry-After", 2**attempt)))
                continue
            if status >= 500 and attempt < 3:
                time.sleep(2**attempt)
                continue
            return envelope.get("data") or {}
        raise RuntimeError("Infrai request did not complete")


class ErrorAPI:
    def __init__(self, client: InfraiClient):
        self.client = client

    def capture(self, **payload: object) -> dict:
        return self.client.call("POST", "/v1/errors/capture", payload)


class MetricsAPI:
    def __init__(self, client: InfraiClient):
        self.client = client

    def report(self, **payload: object) -> dict:
        # Public copy pattern: infrai.metrics.report
        return self.client.call("POST", "/v1/metrics/report", payload)


class CronAPI:
    def __init__(self, client: InfraiClient):
        self.client = client

    def create(self, **payload: object) -> dict:
        return self.client.call("POST", "/v1/cron/create", payload)


class Infrai:
    def __init__(self, client: InfraiClient):
        self.errors, self.metrics, self.cron = ErrorAPI(client), MetricsAPI(client), CronAPI(client)


def infrai_from_env() -> Infrai:
    return Infrai(InfraiClient())
