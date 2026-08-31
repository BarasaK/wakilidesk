from __future__ import annotations

from firms.services import get_active_memberships_for_user


class CurrentFirmMiddleware:
    """Attach a current firm selected from the authenticated user's memberships."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_firm = None
        if request.user.is_authenticated:
            firm_id = request.session.get("current_firm_id")
            memberships = get_active_memberships_for_user(request.user).select_related("firm")
            membership = None
            if firm_id:
                membership = memberships.filter(firm_id=firm_id).first()
            if membership is None:
                membership = memberships.first()
            if membership is not None:
                request.current_firm = membership.firm
                request.session["current_firm_id"] = str(membership.firm_id)

        return self.get_response(request)
