from django import forms

from .models import User


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name"]
        labels = {"name": "Full name"}
        help_texts = {"name": "Shown to people in your organizations."}
        widgets = {"name": forms.TextInput(attrs={"autocomplete": "name"})}
