import pytest

pytestmark = pytest.mark.django_db


def test_settings_requires_login(client):
    response = client.get("/settings/")
    assert response.status_code == 302
    assert response["Location"].startswith("/accounts/login/")


def test_update_name(client, user):
    client.force_login(user)
    response = client.get("/settings/")
    assert response.status_code == 200
    assert b"Full name" in response.content

    response = client.post("/settings/", {"name": "Ama Mensah"}, follow=True)
    assert response.status_code == 200
    assert b"Your profile was saved." in response.content
    user.refresh_from_db()
    assert user.name == "Ama Mensah"


def test_navbar_shows_profile_menu(client, user):
    user.name = "Ama Mensah"
    user.save()
    client.force_login(user)
    response = client.get("/")
    assert b">AM<" in response.content  # avatar initials
    assert b"user@example.com" in response.content
    assert b"/settings/" in response.content


def test_account_pages_use_the_settings_layout(client, user):
    client.force_login(user)
    for url in ["/accounts/email/", "/accounts/password/change/", "/accounts/2fa/"]:
        response = client.get(url)
        assert response.status_code == 200, url
        assert b'aria-label="Settings"' in response.content, url
