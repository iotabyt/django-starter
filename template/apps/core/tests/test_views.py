import pytest

pytestmark = pytest.mark.django_db


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'id="pong"' in response.content


def test_ping_returns_only_the_partial(client):
    response = client.get("/ping/", HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assert b'id="pong"' in response.content
    assert b"<html" not in response.content
