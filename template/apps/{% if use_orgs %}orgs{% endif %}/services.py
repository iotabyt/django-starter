"""All organization logic lives here, so views, the API and the admin share it."""

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.users.models import User

from .models import Invite, Membership, Organization, Role
from .tasks import send_invite_email


class InviteError(Exception):
    """A user-facing reason an invite can't be created or accepted."""


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
