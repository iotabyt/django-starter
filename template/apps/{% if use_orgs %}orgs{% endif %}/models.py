import secrets
from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone

from apps.core.models import TimeStampedModel

INVITE_LIFETIME = timedelta(days=7)


def generate_invite_token() -> str:
    return secrets.token_urlsafe(32)


def default_invite_expiry() -> datetime:
    return timezone.now() + INVITE_LIFETIME


class Role(models.TextChoices):
    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"


class Organization(TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="Membership", related_name="organizations"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Membership(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"], name="orgs_membership_unique_user"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user} in {self.organization} ({self.role})"

    @property
    def can_manage(self) -> bool:
        return self.role in (Role.OWNER, Role.ADMIN)


class Invite(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="invites")
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    token = models.CharField(
        max_length=64, unique=True, default=generate_invite_token, editable=False
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    expires_at = models.DateTimeField(default=default_invite_expiry)
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        constraints = [
            # One pending invite per address per organization.
            models.UniqueConstraint(
                "organization",
                Lower("email"),
                condition=Q(accepted_at__isnull=True),
                name="orgs_invite_unique_pending_email",
            ),
        ]

    def __str__(self) -> str:
        return f"Invite for {self.email} to {self.organization}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_pending(self) -> bool:
        return self.accepted_at is None and not self.is_expired
