from __future__ import annotations

from django.conf import settings


def public_base_url() -> str:
    configured_base_url = getattr(settings, "PUBLIC_BASE_URL", "").strip().rstrip("/")
    if configured_base_url:
        return configured_base_url
    for origin in getattr(settings, "CSRF_TRUSTED_ORIGINS", []):
        origin = origin.strip().rstrip("/")
        if origin and "127.0.0.1" not in origin and "localhost" not in origin:
            return origin
    return ""


def public_absolute_url(path: str, request=None) -> str:
    base_url = public_base_url()
    if base_url:
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{base_url}{path}"
    if request is not None:
        return request.build_absolute_uri(path)
    return path
