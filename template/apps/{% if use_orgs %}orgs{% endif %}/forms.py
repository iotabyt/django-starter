from django import forms

from .models import Role


class OrganizationForm(forms.Form):
    name = forms.CharField(
        max_length=200, widget=forms.TextInput(attrs={"placeholder": "Acme Ltd"})
    )


class InviteForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"placeholder": "name@company.com", "autocomplete": "off"})
    )
    role = forms.ChoiceField(
        choices=[(Role.MEMBER, "Member"), (Role.ADMIN, "Admin")], initial=Role.MEMBER
    )
