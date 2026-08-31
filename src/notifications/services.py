from __future__ import annotations

from django.utils import timezone

from notifications.models import Notification


def notify_user(*, firm, recipient, title: str, message: str, object_type: str = "", object_id: str = "") -> Notification:
    return Notification.objects.create(
        firm=firm,
        recipient=recipient,
        title=title,
        message=message,
        object_type=object_type,
        object_id=str(object_id) if object_id else "",
    )


def notifications_for_user(*, firm, user):
    return Notification.objects.filter(firm=firm, recipient=user)


def unread_count_for_user(*, firm, user) -> int:
    return notifications_for_user(firm=firm, user=user).filter(status=Notification.Status.UNREAD).count()


def mark_read(*, notification, user):
    if notification.recipient_id != user.id:
        raise ValueError("Notification does not belong to user.")
    notification.status = Notification.Status.READ
    notification.read_at = timezone.now()
    notification.save(update_fields=["status", "read_at"])
    return notification
