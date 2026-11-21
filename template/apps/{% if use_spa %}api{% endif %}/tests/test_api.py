import pytest

pytestmark = pytest.mark.django_db


def test_me_requires_a_session(client):
    assert client.get("/api/me").status_code == 401


def test_me(client, user):
    client.force_login(user)
    response = client.get("/api/me")
    assert response.status_code == 200
    assert response.json() == {
        "id": user.pk,
        "email": "user@example.com",
        "name": "",
        "is_staff": False,
        "admin_url": None,
    }


def test_me_includes_admin_url_for_staff(client, user):
    user.is_staff = True
    user.save()
    client.force_login(user)
    assert client.get("/api/me").json()["admin_url"] == "/admin/"
