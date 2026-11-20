from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from procrastinate.contrib.django import app

from .models import Invite


@app.task(queue="emails", retry=3)
def send_invite_email(invite_id: int) -> None:
    invite = (
        Invite.objects.select_related("organization", "invited_by").filter(pk=invite_id).first()
    )
    # Deleted, replaced, accepted or expired since it was queued: nothing to send.
    if invite is None or not invite.is_pending:
        return

    accept_url = settings.SITE_URL + reverse("orgs:accept_invite", args=[invite.token])
    context = {
        "invite": invite,
        "organization": invite.organization,
        "accept_url": accept_url,
        "project_name": settings.PROJECT_NAME,
    }
    send_mail(
        subject=f"You're invited to join {invite.organization.name} on {settings.PROJECT_NAME}",
        message=render_to_string("orgs/email/invite.txt", context),
        from_email=None,
        recipient_list=[invite.email],
    )
