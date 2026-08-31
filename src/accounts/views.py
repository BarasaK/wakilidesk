from __future__ import annotations

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.forms import InvitationAcceptForm, SignupForm
from accounts.models import User
from audit.services import record_audit_event
from firms.models import FirmMembership, UserInvitation


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            record_audit_event(
                request=request,
                user=user,
                action="user_signed_up",
                object_type="User",
                object_id=user.id,
            )
            return redirect("firm_onboarding")
    else:
        form = SignupForm()

    return render(request, "accounts/signup.html", {"form": form})


def accept_invitation(request, token):
    invitation = _invitation_from_token(token)
    if invitation is None or invitation.status != UserInvitation.Status.PENDING:
        return render(request, "accounts/invitation_invalid.html", status=400)

    existing_user = User.objects.filter(email__iexact=invitation.email).first()
    if request.method == "POST":
        if existing_user is not None:
            user = existing_user
            FirmMembership.objects.get_or_create(
                user=user,
                firm=invitation.firm,
                defaults={
                    "role": invitation.role,
                    "status": FirmMembership.Status.ACTIVE,
                },
            )
            invitation.status = UserInvitation.Status.ACCEPTED
            invitation.accepted_by = user
            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=["status", "accepted_by", "accepted_at", "updated_at"])
            record_audit_event(
                request=request,
                firm=invitation.firm,
                user=user,
                action="user_invitation_accepted",
                object_type="UserInvitation",
                object_id=invitation.id,
            )
            login(request, user)
            return redirect("dashboard")

        form = InvitationAcceptForm(request.POST, email=invitation.email)
        if form.is_valid():
            user = form.save()
            FirmMembership.objects.create(
                user=user,
                firm=invitation.firm,
                role=invitation.role,
                status=FirmMembership.Status.ACTIVE,
            )
            invitation.status = UserInvitation.Status.ACCEPTED
            invitation.accepted_by = user
            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=["status", "accepted_by", "accepted_at", "updated_at"])
            record_audit_event(
                request=request,
                firm=invitation.firm,
                user=user,
                action="user_invitation_accepted",
                object_type="UserInvitation",
                object_id=invitation.id,
            )
            login(request, user)
            return redirect("dashboard")
    else:
        form = None if existing_user is not None else InvitationAcceptForm(email=invitation.email)

    return render(
        request,
        "accounts/accept_invitation.html",
        {"invitation": invitation, "form": form, "existing_user": existing_user},
    )


@login_required
def switch_firm(request, firm_id):
    membership = get_object_or_404(
        FirmMembership,
        user=request.user,
        firm_id=firm_id,
        status=FirmMembership.Status.ACTIVE,
        firm__is_active=True,
    )
    request.session["current_firm_id"] = str(membership.firm_id)
    record_audit_event(
        request=request,
        firm=membership.firm,
        action="firm_switched",
        object_type="Firm",
        object_id=membership.firm_id,
    )
    return redirect("dashboard")


def _invitation_from_token(token):
    signer = TimestampSigner()
    try:
        invitation_id = signer.unsign(token, max_age=60 * 60 * 24 * 14)
    except (BadSignature, SignatureExpired):
        return None
    return UserInvitation.objects.filter(id=invitation_id).select_related("firm", "role").first()
