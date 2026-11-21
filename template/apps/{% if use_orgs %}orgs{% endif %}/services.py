"""All organization logic lives here, so views, the API and the admin share it."""

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.users.models import User

from .models import Invite, Membership, Organization, Role
from .tasks import send_invite_email


class InviteError(Exception):
    """A user-facing reason an invite can't be created or accepted."""


class MembershipError(Exception):
    """A user-facing reason a membership change isn't allowed."""


class NotAllowed(MembershipError):
    """The acting user doesn't have the role needed for this change."""


def get_membership(user: User, slug: str) -> Membership | None:
    """The user's membership in the organization with this slug, if any."""
    return (
        Membership.objects.filter(organization__slug=slug, user=user)
        .select_related("organization")
        .first()
    )


def _actor(organization: Organization, user: User) -> Membership:
    # Lock the organization's memberships so concurrent changes can't remove the last owner.
    memberships = list(Membership.objects.select_for_update().filter(organization=organization))
    for membership in memberships:
        if membership.user_id == user.pk:
            return membership
    raise NotAllowed("You're not a member of this organization.")


def _owner_count(organization: Organization) -> int:
    return organization.memberships.filter(role=Role.OWNER).count()


def _unique_slug(name: str) -> str:
    base = slugify(name)[:200] or "org"
    slug, n = base, 2
    while Organization.objects.filter(slug=slug).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


@transaction.atomic
def create_organization(name: str, owner: User) -> Organization:
    organization = Organization.objects.create(name=name, slug=_unique_slug(name), created_by=owner)
    Membership.objects.create(organization=organization, user=owner, role=Role.OWNER)
    return organization


@transaction.atomic
def invite_member(
    organization: Organization, email: str, invited_by: User, role: str = Role.MEMBER
) -> Invite:
    email = email.strip().lower()
    if organization.memberships.filter(user__email__iexact=email).exists():
        raise InviteError(f"{email} is already a member of {organization.name}.")

    # Re-inviting replaces any earlier pending (or expired) invite with a fresh link.
    organization.invites.filter(email__iexact=email, accepted_at__isnull=True).delete()
    invite = Invite.objects.create(
        organization=organization, email=email, role=role, invited_by=invited_by
    )
    invite_id = invite.pk
    transaction.on_commit(lambda: send_invite_email.defer(invite_id=invite_id))
    return invite


@transaction.atomic
def accept_invite(token: str, user: User) -> Membership:
    invite = (
        Invite.objects.select_for_update()
        .select_related("organization")
        .filter(token=token)
        .first()
    )
    if invite is None:
        raise InviteError("This invite link isn't valid.")
    if invite.accepted_at is not None:
        raise InviteError("This invite has already been used.")
    if invite.is_expired:
        raise InviteError("This invite has expired. Ask for a new one.")
    if invite.email.lower() != user.email.lower():
        raise InviteError(
            f"This invite was sent to {invite.email}. Sign in with that address to accept it."
        )

    membership, _ = Membership.objects.get_or_create(
        organization=invite.organization, user=user, defaults={"role": invite.role}
    )
    invite.accepted_at = timezone.now()
    invite.accepted_by = user
    invite.save(update_fields=["accepted_at", "accepted_by", "updated_at"])
    return membership


@transaction.atomic
def change_role(membership: Membership, role: str, by: User) -> Membership:
    """Owners can change any role; admins can switch people between admin and member."""
    actor = _actor(membership.organization, by)
    if role not in Role.values:
        raise MembershipError("Choose owner, admin or member.")
    if not actor.can_manage:
        raise NotAllowed("Only owners and admins can change roles.")
    if Role.OWNER in (role, membership.role) and actor.role != Role.OWNER:
        raise NotAllowed("Only owners can grant or remove the owner role.")
    if (
        membership.role == Role.OWNER
        and role != Role.OWNER
        and _owner_count(membership.organization) == 1
    ):
        raise MembershipError("An organization needs at least one owner.")
    membership.role = role
    membership.save(update_fields=["role", "updated_at"])
    return membership


@transaction.atomic
def remove_member(membership: Membership, by: User) -> None:
    """Remove someone (owners/admins), or leave (anyone). The last owner can't go."""
    actor = _actor(membership.organization, by)
    leaving = membership.pk == actor.pk
    if not leaving:
        if not actor.can_manage:
            raise NotAllowed("Only owners and admins can remove members.")
        if membership.role == Role.OWNER and actor.role != Role.OWNER:
            raise NotAllowed("Only owners can remove an owner.")
    if membership.role == Role.OWNER and _owner_count(membership.organization) == 1:
        raise MembershipError(
            "An organization needs at least one owner. Make someone else an owner first."
        )
    membership.delete()


@transaction.atomic
def revoke_invite(invite: Invite, by: User) -> None:
    actor = _actor(invite.organization, by)
    if not actor.can_manage:
        raise NotAllowed("Only owners and admins can revoke invites.")
    if invite.accepted_at is not None:
        raise MembershipError("That invite has already been accepted.")
    invite.delete()
