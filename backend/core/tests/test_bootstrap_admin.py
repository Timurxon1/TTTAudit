import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.django_db
def test_bootstrap_admin_creates_and_updates_superuser(monkeypatch):
    monkeypatch.setenv("DJANGO_ADMIN_USERNAME", "TTTaudit")
    monkeypatch.setenv("DJANGO_ADMIN_PASSWORD", "first-password")
    call_command("bootstrap_admin")

    user = get_user_model().objects.get(username="TTTaudit")
    assert user.is_active and user.is_staff and user.is_superuser
    assert user.check_password("first-password")

    monkeypatch.setenv("DJANGO_ADMIN_PASSWORD", "second-password")
    call_command("bootstrap_admin")
    user.refresh_from_db()
    assert user.check_password("second-password")


@pytest.mark.django_db
def test_bootstrap_admin_is_noop_without_secrets(monkeypatch):
    monkeypatch.delenv("DJANGO_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("DJANGO_ADMIN_PASSWORD", raising=False)
    call_command("bootstrap_admin")
    assert not get_user_model().objects.exists()


@pytest.mark.django_db
def test_bootstrap_admin_requires_both_secrets(monkeypatch):
    monkeypatch.setenv("DJANGO_ADMIN_USERNAME", "TTTaudit")
    monkeypatch.delenv("DJANGO_ADMIN_PASSWORD", raising=False)
    with pytest.raises(CommandError):
        call_command("bootstrap_admin")
