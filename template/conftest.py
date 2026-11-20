import pytest


@pytest.fixture
def user(db):
    from apps.users.models import User

    return User.objects.create_user(email="user@example.com", password="correct-horse-battery")
