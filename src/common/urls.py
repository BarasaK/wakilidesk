from __future__ import annotations

from django.conf import settings


def public_absolute_url(path: str, request=None) -> str:
    base_url = getattr(settings, "PUBLIC_BASE_URL", "").strip().rstrip("/")
    if base_url:
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{base_url}{path}"
    if request is not None:
        return request.build_absolute_uri(path)
    return path
