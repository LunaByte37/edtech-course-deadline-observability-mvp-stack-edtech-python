"""Course deadline decision and its observability calls."""
from dataclasses import dataclass
from datetime import date

from .infrai_client import Infrai


@dataclass(frozen=True)
class DeadlineRequest:
    course_id: str
    learner_id: str
    due_on: date
    submitted_on: date | None


@dataclass(frozen=True)
class DeadlineResult:
    status: str
    days_late: int


def assess_deadline(request: DeadlineRequest, observability: Infrai | None = None) -> DeadlineResult:
    if request.submitted_on is None:
        result = DeadlineResult("open", 0)
    else:
        late = max(0, (request.submitted_on - request.due_on).days)
        result = DeadlineResult("late" if late else "on_time", late)
    if observability:
        try:
            observability.metrics.report(
                name="course_deadline_assessed",
                value=result.days_late,
                type="gauge",
                tags={"course_id": request.course_id, "status": result.status},
            )
        except Exception as exc:
            observability.errors.capture(
                title="course deadline reporting failed",
                message=str(exc),
                level="error",
                exception={"type": type(exc).__name__, "message": str(exc)},
                fingerprint=["course_delivery", "deadline_reporting"],
            )
    return result
