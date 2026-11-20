from django.http import HttpRequest

from apps.users.models import User


class AuthenticatedHttpRequest(HttpRequest):
    """For views behind @login_required, so `request.user` is typed as a real User."""

    user: User  # pyright: ignore[reportIncompatibleVariableOverride]
