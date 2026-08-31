from __future__ import annotations

from contextvars import ContextVar


_current_firm_id: ContextVar[str | None] = ContextVar("current_firm_id", default=None)


def set_current_firm_id(firm_id: str | None):
    return _current_firm_id.set(firm_id)


def get_current_firm_id() -> str | None:
    return _current_firm_id.get()


def reset_current_firm_id(token) -> None:
    _current_firm_id.reset(token)
