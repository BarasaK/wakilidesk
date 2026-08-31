from __future__ import annotations

from audit.models import AuditEvent


def record_audit_event(
    *,
    request=None,
    firm=None,
    user=None,
    action: str,
    object_type: str = "",
    object_id: str = "",
    metadata: dict | None = None,
) -> AuditEvent:
    actor = user
    if request is not None and getattr(request, "user", None) is not None:
        if request.user.is_authenticated:
            actor = request.user

    return AuditEvent.objects.create(
        firm=firm,
        user=actor,
        action=action,
        object_type=object_type,
        object_id=str(object_id) if object_id else "",
        ip_address=_ip_from_request(request),
        user_agent=_user_agent_from_request(request),
        metadata=metadata or {},
    )


def _ip_from_request(request):
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _user_agent_from_request(request) -> str:
    if request is None:
        return ""
    return request.META.get("HTTP_USER_AGENT", "")
