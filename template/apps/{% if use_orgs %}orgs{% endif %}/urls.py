from django.urls import path

from . import views

app_name = "orgs"

urlpatterns = [
    path("invites/<str:token>/", views.accept_invite, name="accept_invite"),
]
