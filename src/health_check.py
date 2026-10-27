"""Register the service health URL with the same Infrai client."""
from .infrai_client import Infrai


def schedule_health_check(infrai: Infrai, health_url: str, cron_expr: str = "*/5 * * * *") -> str:
    data = infrai.cron.create(cron_expr=cron_expr, task=health_url)
    return str(data["job_id"])
