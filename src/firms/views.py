from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse

from firms.services import get_firm_for_user_or_404


@login_required
def dashboard(request):
    if request.current_firm is None:
        return HttpResponse("No active firm membership found.", status=403)
    return HttpResponse(f"wakiliDesk dashboard: {request.current_firm.display_name}")


@login_required
def firm_detail(request, firm_id):
    try:
        firm = get_firm_for_user_or_404(request.user, firm_id)
    except PermissionDenied:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    return JsonResponse(
        {
            "id": str(firm.id),
            "display_name": firm.display_name,
            "country": firm.country,
            "timezone": firm.timezone,
            "currency": firm.currency,
        }
    )
