import pytest
from django.db import OperationalError


@pytest.mark.django_db
def test_up_skips_host_validation_and_https_redirect(client, settings):
    settings.ALLOWED_HOSTS = ["example.com"]
    settings.SECURE_SSL_REDIRECT = True
    # kamal-proxy polls over plain HTTP with the container IP as Host.
    response = client.get("/up", HTTP_HOST="172.18.0.5:8000")
    assert response.status_code == 200
    assert response.content == b"ok"


def test_up_returns_503_when_the_database_is_down(client, monkeypatch):
    def broken_cursor():
        raise OperationalError("connection refused")

    monkeypatch.setattr("apps.core.middleware.connection.cursor", broken_cursor)
    response = client.get("/up")
    assert response.status_code == 503
