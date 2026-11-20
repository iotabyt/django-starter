from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Invite, Membership, Organization


class MembershipInline(TabularInline):
    model = Membership
    extra = 0
    autocomplete_fields = ["user"]


class InviteInline(TabularInline):
    model = Invite
    extra = 0
    fields = ("email", "role", "invited_by", "expires_at", "accepted_at")
    readonly_fields = ("accepted_at",)
    autocomplete_fields = ["invited_by"]


@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    list_display = ("name", "slug", "created_by", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["created_by"]
    inlines = [MembershipInline, InviteInline]


@admin.register(Membership)
class MembershipAdmin(ModelAdmin):
    list_display = ("user", "organization", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__email", "organization__name")
    autocomplete_fields = ["organization", "user"]


@admin.register(Invite)
class InviteAdmin(ModelAdmin):
    list_display = ("email", "organization", "role", "expires_at", "accepted_at")
    list_filter = ("role",)
    search_fields = ("email", "organization__name")
    autocomplete_fields = ["organization", "invited_by", "accepted_by"]
    readonly_fields = ("token", "accepted_at", "accepted_by")
