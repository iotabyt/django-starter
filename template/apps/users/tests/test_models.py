import pytest
from django.db import IntegrityError, transaction

from apps.users.models import User

pytestmark = pytest.mark.django_db


def test_email_is_lowercased():
    user = User.objects.create_user(email="Frank@Example.COM", password="pw-123456")
    assert user.email == "frank@example.com"


def test_email_is_unique_case_insensitively():
    User.objects.create_user(email="a@example.com", password="pw-123456")
    User.objects.create_user(email="b@example.com", password="pw-123456")
    # .update() skips the manager, so this hits the Lower("email") constraint directly.
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.filter(email="b@example.com").update(email="A@example.com")


def test_create_superuser():
    admin = User.objects.create_superuser(email="admin@example.com", password="pw-123456")
    assert admin.is_staff
    assert admin.is_superuser
    assert admin.check_password("pw-123456")


def test_names_come_from_name_field():
    user = User(email="ama@example.com", name="Ama Mensah")
    assert user.get_full_name() == "Ama Mensah"
    assert user.get_short_name() == "Ama"
    assert str(user) == "ama@example.com"
