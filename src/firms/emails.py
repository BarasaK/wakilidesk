from __future__ import annotations

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from firms.models import UserInvitation


def send_user_invitation_email(*, invitation: UserInvitation, request) -> None:
    accept_url = request.build_absolute_uri(
        reverse("accept_invitation", args=[invitation.token])
    )
    context = {
        "accept_url": accept_url,
        "firm": invitation.firm,
        "invitation": invitation,
        "invited_by": invitation.invited_by,
    }
    subject = render_to_string("firms/email/invitation_subject.txt", context).strip()
    text_body = render_to_string("firms/email/invitation.txt", context)
    html_body = render_to_string("firms/email/invitation.html", context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[invitation.email],
    )
    message.attach_alternative(html_body, "text/html")
    message.send()
