import pytest

pytestmark = pytest.mark.django_db


def test_me_requires_a_session(client):
    assert client.get("/api/me").status_code == 401


def test_me(client, user):
    client.force_login(user)
    response = client.get("/api/me")
    assert response.status_code == 200
    assert response.json() == {"id": user.pk, "email": "user@example.com", "name": ""}
