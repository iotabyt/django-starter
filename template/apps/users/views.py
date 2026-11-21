from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render

from apps.core.types import AuthenticatedHttpRequest

from .forms import ProfileForm


@login_required
def profile(request: AuthenticatedHttpRequest) -> HttpResponse:
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile was saved.")
        return redirect("users:settings")
    return render(request, "settings/profile.html", {"form": form})
