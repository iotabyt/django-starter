from django.urls import reverse
from ninja import Schema


class MeOut(Schema):
    id: int
    email: str
    name: str
    is_staff: bool
    # Where the admin lives (ADMIN_URL can move it); only for staff.
    admin_url: str | None = None

    @staticmethod
    def resolve_admin_url(obj) -> str | None:
        return reverse("admin:index") if obj.is_staff else None


class ErrorOut(Schema):
    detail: str
