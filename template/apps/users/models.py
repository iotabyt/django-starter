from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower

from .managers import UserManager


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None
    email = models.EmailField("email address", unique=True)
    name = models.CharField("name", max_length=255, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    # ClassVar stops pyright from using Django's create_superuser(username, ...) signature.
    objects: ClassVar[UserManager] = UserManager()  # pyright: ignore[reportIncompatibleVariableOverride]

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("email"), name="users_user_email_ci_unique"),
        ]

    def __str__(self) -> str:
        return self.email

    def clean(self) -> None:
        super().clean()
        # Forms (admin, allauth) don't go through the manager, so normalise here too.
        self.email = self.email.lower()

    def get_full_name(self) -> str:
        return self.name.strip()

    def get_short_name(self) -> str:
        return self.name.strip().split(" ")[0] if self.name.strip() else ""
