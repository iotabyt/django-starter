from datetime import timedelta

import pytest
from django.utils import timezone
from procrastinate.contrib.django.models import ProcrastinateJob

from apps.orgs.models import Invite, Membership, Role
from apps.orgs.services import InviteError, accept_invite, create_organization, invite_member
from apps.users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner():
    return User.objects.create_user(email="owner@example.com", password="pw-123456")


@pytest.fixture
def org(owner):
    return create_organization("Acme Ltd", owner)


def test_creator_becomes_owner(org, owner):
    membership = Membership.objects.get(organization=org, user=owner)
    assert membership.role == Role.OWNER
    assert membership.can_manage
    assert org.slug == "acme-ltd"


def test_slugs_stay_unique(owner):
    slugs = [create_organization("Acme Ltd", owner).slug for _ in range(3)]
    assert slugs == ["acme-ltd", "acme-ltd-2", "acme-ltd-3"]


def test_invite_and_accept(org, owner, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        invite = invite_member(org, "New@Example.com", owner, Role.ADMIN)
    assert invite.email == "new@example.com"
    assert len(callbacks) == 1
    assert ProcrastinateJob.objects.filter(
        task_name="apps.orgs.tasks.send_invite_email", queue_name="emails"
    ).exists()

    member = User.objects.create_user(email="new@example.com", password="pw-123456")
    membership = accept_invite(invite.token, member)
    assert membership.role == Role.ADMIN
    invite.refresh_from_db()
    assert invite.accepted_by == member
    assert not invite.is_pending

    with pytest.raises(InviteError, match="already been used"):
        accept_invite(invite.token, member)


def test_reinvite_replaces_the_pending_invite(org, owner):
    first = invite_member(org, "new@example.com", owner)
    second = invite_member(org, "NEW@example.com", owner)
    assert first.token != second.token
    assert list(Invite.objects.filter(organization=org)) == [second]


def test_wrong_email_is_rejected(org, owner):
    invite = invite_member(org, "right@example.com", owner)
    other = User.objects.create_user(email="wrong@example.com", password="pw-123456")
    with pytest.raises(InviteError, match=r"sent to right@example\.com"):
        accept_invite(invite.token, other)


def test_email_match_is_case_insensitive(org, owner):
    invite = invite_member(org, "Mixed@Example.com", owner)
    member = User.objects.create_user(email="mixed@example.com", password="pw-123456")
    assert accept_invite(invite.token, member).organization == org


def test_expired_invite_is_rejected(org, owner):
    invite = invite_member(org, "late@example.com", owner)
    Invite.objects.filter(pk=invite.pk).update(expires_at=timezone.now() - timedelta(minutes=1))
    member = User.objects.create_user(email="late@example.com", password="pw-123456")
    with pytest.raises(InviteError, match="expired"):
        accept_invite(invite.token, member)


def test_existing_member_cannot_be_invited(org, owner):
    with pytest.raises(InviteError, match="already a member"):
        invite_member(org, "OWNER@example.com", owner)
