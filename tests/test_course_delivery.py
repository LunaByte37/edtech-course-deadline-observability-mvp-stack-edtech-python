from datetime import date

from src.course_delivery import DeadlineRequest, assess_deadline


def test_late_submission_is_visible_to_educator_reporting():
    request = DeadlineRequest("writing-101", "learner-7", date(2026, 10, 20), date(2026, 10, 22))
    assert assess_deadline(request) .status == "late"
    assert assess_deadline(request).days_late == 2
