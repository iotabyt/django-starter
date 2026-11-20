import pytest
from django.core import mail

from apps.orgs.services import create_organization, invite_member
from apps.orgs.tasks import send_invite_email
from apps.users.models import User

pytestmark = pytest.mark.django_db


def test_send_invite_email(settings):
    settings.SITE_URL = "https://app.example.com"
    owner = User.objects.create_user(email="owner@example.com", password="pw-123456")
    org = create_organization("Acme & Sons", owner)
    invite = invite_member(org, "new@example.com", owner)

    send_invite_email(invite_id=invite.pk)

    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ["new@example.com"]
    assert "Acme & Sons" in message.subject
    assert f"https://app.example.com/orgs/invites/{invite.token}/" in message.body
    assert "&amp;" not in message.body


def test_send_invite_email_skips_accepted_invites():
    owner = User.objects.create_user(email="owner@example.com", password="pw-123456")
    org = create_organization("Acme", owner)
    invite = invite_member(org, "owner2@example.com", owner)
    invite.accepted_by = owner
    invite.accepted_at = invite.created_at
    invite.save()

    send_invite_email(invite_id=invite.pk)

    assert mail.outbox == []
