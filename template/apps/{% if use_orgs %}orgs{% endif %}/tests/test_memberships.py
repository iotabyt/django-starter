import pytest

from apps.orgs.models import Invite, Membership, Role
from apps.orgs.services import (
    MembershipError,
    NotAllowed,
    change_role,
    create_organization,
    invite_member,
    remove_member,
    revoke_invite,
)
from apps.users.models import User

pytestmark = pytest.mark.django_db


def make_user(email):
    return User.objects.create_user(email=email, password="pw-123456")


@pytest.fixture
def team():
    owner = make_user("owner@example.com")
    org = create_organization("Acme", owner)
    admin = make_user("admin@example.com")
    member = make_user("member@example.com")
    m_admin = Membership.objects.create(organization=org, user=admin, role=Role.ADMIN)
    m_member = Membership.objects.create(organization=org, user=member, role=Role.MEMBER)
    m_owner = Membership.objects.get(organization=org, user=owner)
    return {
        "org": org,
        "owner": owner,
        "admin": admin,
        "member": member,
        "m_owner": m_owner,
        "m_admin": m_admin,
        "m_member": m_member,
    }


def test_owner_can_promote_to_owner_and_back(team):
    change_role(team["m_admin"], Role.OWNER, team["owner"])
    assert Membership.objects.get(pk=team["m_admin"].pk).role == Role.OWNER
    # With two owners, the original one can step down.
    change_role(team["m_owner"], Role.MEMBER, team["owner"])
    assert Membership.objects.get(pk=team["m_owner"].pk).role == Role.MEMBER


def test_admin_can_switch_admin_and_member(team):
    change_role(team["m_member"], Role.ADMIN, team["admin"])
    assert Membership.objects.get(pk=team["m_member"].pk).role == Role.ADMIN


def test_admin_cannot_touch_the_owner_role(team):
    with pytest.raises(NotAllowed, match="Only owners"):
        change_role(team["m_member"], Role.OWNER, team["admin"])
    with pytest.raises(NotAllowed, match="Only owners"):
        change_role(team["m_owner"], Role.MEMBER, team["admin"])


def test_member_cannot_change_roles(team):
    with pytest.raises(NotAllowed):
        change_role(team["m_admin"], Role.MEMBER, team["member"])


def test_last_owner_cannot_step_down(team):
    with pytest.raises(MembershipError, match="at least one owner"):
        change_role(team["m_owner"], Role.ADMIN, team["owner"])


def test_unknown_role_is_rejected(team):
    with pytest.raises(MembershipError, match="Choose owner, admin or member"):
        change_role(team["m_member"], "superhero", team["owner"])


def test_outsider_cannot_change_anything(team):
    outsider = make_user("outsider@example.com")
    with pytest.raises(NotAllowed, match="not a member"):
        change_role(team["m_member"], Role.ADMIN, outsider)


def test_admin_removes_member_but_not_owner(team):
    remove_member(team["m_member"], team["admin"])
    assert not Membership.objects.filter(pk=team["m_member"].pk).exists()
    with pytest.raises(NotAllowed, match="Only owners can remove an owner"):
        remove_member(team["m_owner"], team["admin"])


def test_member_cannot_remove_others_but_can_leave(team):
    with pytest.raises(NotAllowed):
        remove_member(team["m_admin"], team["member"])
    remove_member(team["m_member"], team["member"])
    assert not Membership.objects.filter(pk=team["m_member"].pk).exists()


def test_last_owner_cannot_leave(team):
    with pytest.raises(MembershipError, match="at least one owner"):
        remove_member(team["m_owner"], team["owner"])


def test_revoke_invite(team):
    invite = invite_member(team["org"], "new@example.com", team["owner"])
    with pytest.raises(NotAllowed):
        revoke_invite(invite, team["member"])
    revoke_invite(invite, team["admin"])
    assert not Invite.objects.filter(pk=invite.pk).exists()
