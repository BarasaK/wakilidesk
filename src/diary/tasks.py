from __future__ import annotations

from celery import shared_task

from diary.services import send_due_diary_reminders


@shared_task
def send_diary_reminders() -> dict[str, int]:
    return send_due_diary_reminders()
