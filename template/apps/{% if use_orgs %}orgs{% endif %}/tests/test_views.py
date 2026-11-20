import pytest

from apps.orgs.models import Membership
from apps.orgs.services import create_organization, invite_member
from apps.users.models import User

pytestmark = pytest.mark.django_db


def test_accept_invite_view(client, settings):
    owner = User.objects.create_user(email="owner@example.com", password="pw-123456")
    org = create_organization("Acme", owner)
    invite = invite_member(org, "new@example.com", owner)
    member = User.objects.create_user(email="new@example.com", password="pw-123456")
    url = f"/orgs/invites/{invite.token}/"

    # Anonymous visitors are sent to log in first.
    assert client.get(url).status_code == 302

    client.force_login(member)
    response = client.get(url)
    assert response.status_code == 200
    assert b"Acme" in response.content
    assert b"Accept invite" in response.content

    response = client.post(url)
    assert response.status_code == 302
    assert response["Location"] == settings.LOGIN_REDIRECT_URL
    assert Membership.objects.filter(organization=org, user=member).exists()

    # A second accept shows the error instead.
    response = client.post(url)
    assert response.status_code == 400
    assert b"already been used" in response.content


def test_unknown_token_is_404(client, user):
    client.force_login(user)
    assert client.get("/orgs/invites/nope/").status_code == 404
