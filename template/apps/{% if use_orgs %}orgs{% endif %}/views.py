from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.types import AuthenticatedHttpRequest

from . import services
from .models import Invite


@login_required
def accept_invite(request: AuthenticatedHttpRequest, token: str) -> HttpResponse:
    invite = get_object_or_404(
        Invite.objects.select_related("organization", "invited_by"), token=token
    )
    error = None
    if request.method == "POST":
        try:
            services.accept_invite(token, request.user)
        except services.InviteError as exc:
            error = str(exc)
        else:
            messages.success(request, f"You've joined {invite.organization.name}.")
            return redirect(settings.LOGIN_REDIRECT_URL)

    return render(
        request,
        "orgs/accept_invite.html",
        {"invite": invite, "error": error},
        status=400 if error else 200,
    )
