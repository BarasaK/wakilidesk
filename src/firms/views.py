from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from audit.services import record_audit_event
from diary.models import DiaryEvent
from diary.services import diary_events_visible_to_user
from documents.services import documents_visible_to_user
from firms.forms import FirmOnboardingForm, FirmProfileForm, RoleForm, UserInvitationForm
from firms.models import Firm, FirmMembership, Role, UserInvitation
from firms.services import (
    ensure_default_roles_for_firm,
    get_active_memberships_for_user,
    get_firm_for_user_or_404,
    require_firm_permission,
)
from notifications.services import unread_count_for_user
from physical_files.models import PhysicalFile
from physical_files.services import overdue_checkouts_visible_to_user, physical_files_visible_to_user
from matters.services import matters_visible_to_user


@login_required
def dashboard(request):
    if request.current_firm is None:
        return redirect("firm_onboarding")
    memberships = get_active_memberships_for_user(request.user).select_related("firm", "role")
    firm = request.current_firm
    visible_matters = matters_visible_to_user(firm=firm, user=request.user)
    visible_documents = documents_visible_to_user(firm=firm, user=request.user)
    visible_physical_files = physical_files_visible_to_user(firm=firm, user=request.user)
    visible_diary_events = diary_events_visible_to_user(firm=firm, user=request.user)
    now = timezone.now()
    digitisation_total = visible_physical_files.count()
    digitisation_completed = visible_physical_files.filter(
        digitisation_status=PhysicalFile.DigitisationStatus.COMPLETED
    ).count()
    digitisation_percent = (
        round((digitisation_completed / digitisation_total) * 100)
        if digitisation_total
        else 0
    )
    metrics = {
        "active_matters": visible_matters.filter(status__in=["OPEN", "ACTIVE"]).count(),
        "documents_total": visible_documents.count(),
        "physical_files_checked_out": visible_physical_files.filter(status=PhysicalFile.Status.CHECKED_OUT).count(),
        "files_awaiting_return": overdue_checkouts_visible_to_user(firm=firm, user=request.user).count(),
        "digitisation_total": digitisation_total,
        "digitisation_completed": digitisation_completed,
        "digitisation_percent": digitisation_percent,
        "digitisation_quality_review": visible_physical_files.filter(digitisation_status=PhysicalFile.DigitisationStatus.QUALITY_REVIEW).count(),
        "diary_upcoming": visible_diary_events.filter(
            status=DiaryEvent.Status.SCHEDULED,
            start_at__gte=now,
        ).count(),
        "diary_overdue": visible_diary_events.filter(
            status=DiaryEvent.Status.SCHEDULED,
            start_at__lt=now,
        ).count(),
        "unread_notifications": unread_count_for_user(firm=firm, user=request.user),
    }
    upcoming_diary_events = visible_diary_events.filter(
        status=DiaryEvent.Status.SCHEDULED,
        start_at__gte=now,
    )[:5]
    return render(
        request,
        "dashboard/home.html",
        {
            "firm": firm,
            "memberships": memberships,
            "metrics": metrics,
            "upcoming_diary_events": upcoming_diary_events,
        },
    )


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


@login_required
def firm_onboarding(request):
    if get_active_memberships_for_user(request.user).exists():
        return redirect("dashboard")

    if request.method == "POST":
        form = FirmOnboardingForm(request.POST, request.FILES)
        if form.is_valid():
            firm = form.save()
            roles = ensure_default_roles_for_firm(firm)
            FirmMembership.objects.create(
                user=request.user,
                firm=firm,
                role=roles["Firm Administrator"],
                status=FirmMembership.Status.ACTIVE,
            )
            request.session["current_firm_id"] = str(firm.id)
            record_audit_event(
                request=request,
                firm=firm,
                action="firm_created",
                object_type="Firm",
                object_id=firm.id,
            )
            messages.success(request, "Firm workspace created.")
            return redirect("dashboard")
    else:
        form = FirmOnboardingForm(
            initial={
                "country": "Kenya",
                "timezone": "Africa/Nairobi",
                "currency": "KES",
                "file_number_pattern": "{PRACTICE_AREA}/{YEAR}/{SEQUENCE}",
            }
        )

    return render(request, "firms/onboarding.html", {"form": form})


@login_required
def firm_profile(request):
    firm = _current_firm_or_redirect(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "manage_firm_settings")
    if request.method == "POST":
        form = FirmProfileForm(request.POST, request.FILES, instance=firm)
        if form.is_valid():
            form.save()
            record_audit_event(
                request=request,
                firm=firm,
                action="firm_profile_updated",
                object_type="Firm",
                object_id=firm.id,
            )
            messages.success(request, "Firm profile updated.")
            return redirect("firm_profile")
    else:
        form = FirmProfileForm(instance=firm)
    return render(request, "firms/profile.html", {"firm": firm, "form": form})


@login_required
def admin_users(request):
    firm = _current_firm_or_redirect(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "manage_users")
    memberships = firm.memberships.select_related("user", "role").order_by("user__email")
    invitations = firm.invitations.select_related("role", "invited_by").order_by("-created_at")
    return render(
        request,
        "firms/admin_users.html",
        {"firm": firm, "memberships": memberships, "invitations": invitations},
    )


@login_required
def invite_user(request):
    firm = _current_firm_or_redirect(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "manage_users")
    if request.method == "POST":
        form = UserInvitationForm(request.POST, firm=firm)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.firm = firm
            invitation.invited_by = request.user
            invitation.save()
            record_audit_event(
                request=request,
                firm=firm,
                action="user_invited",
                object_type="UserInvitation",
                object_id=invitation.id,
                metadata={"email": invitation.email, "role": invitation.role.name},
            )
            messages.success(request, "Invitation created.")
            return redirect("admin_users")
    else:
        form = UserInvitationForm(firm=firm)
    return render(request, "firms/invite_user.html", {"firm": firm, "form": form})


@login_required
def roles_list(request):
    firm = _current_firm_or_redirect(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "manage_roles")
    roles = firm.roles.prefetch_related("permissions").order_by("name")
    return render(request, "firms/roles_list.html", {"firm": firm, "roles": roles})


@login_required
def role_create(request):
    firm = _current_firm_or_redirect(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "manage_roles")
    if request.method == "POST":
        form = RoleForm(request.POST, firm=firm)
        if form.is_valid():
            role = form.save()
            record_audit_event(
                request=request,
                firm=firm,
                action="role_created",
                object_type="Role",
                object_id=role.id,
            )
            messages.success(request, "Role created.")
            return redirect("roles_list")
    else:
        form = RoleForm(firm=firm)
    return render(request, "firms/role_form.html", {"firm": firm, "form": form})


@login_required
def role_edit(request, role_id):
    firm = _current_firm_or_redirect(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "manage_roles")
    role = get_object_or_404(Role, id=role_id, firm=firm)
    if request.method == "POST":
        form = RoleForm(request.POST, firm=firm, instance=role)
        if form.is_valid():
            form.save()
            record_audit_event(
                request=request,
                firm=firm,
                action="role_updated",
                object_type="Role",
                object_id=role.id,
            )
            messages.success(request, "Role updated.")
            return redirect("roles_list")
    else:
        form = RoleForm(firm=firm, instance=role)
    return render(request, "firms/role_form.html", {"firm": firm, "form": form, "role": role})


def _current_firm_or_redirect(request):
    if request.current_firm is None:
        return None
    return request.current_firm
