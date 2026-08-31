from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from notifications.models import Notification
from notifications.services import mark_read, notifications_for_user


@login_required
def notification_list(request):
    firm = request.current_firm
    if firm is None:
        return redirect("firm_onboarding")
    notifications = notifications_for_user(firm=firm, user=request.user)
    return render(request, "notifications/list.html", {"firm": firm, "notifications": notifications})


@login_required
def notification_mark_read(request, notification_id):
    firm = request.current_firm
    if firm is None:
        return redirect("firm_onboarding")
    notification = get_object_or_404(Notification, id=notification_id, firm=firm, recipient=request.user)
    if request.method == "POST":
        mark_read(notification=notification, user=request.user)
    return redirect("notification_list")
