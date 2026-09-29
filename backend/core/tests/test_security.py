import os
import subprocess
import sys

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import override_settings

from core.models import Credential, Lead, StaffCertificate


@pytest.fixture
def lead_with_file(db):
    lead = Lead(name="Test", phone="+998901234567")
    lead.attachment.save("smeta.pdf", ContentFile(b"%PDF-1.4 test"), save=True)
    return lead


def test_media_root_is_isolated_from_local_media():
    assert os.path.realpath(settings.MEDIA_ROOT) != os.path.realpath(settings.BASE_DIR / "media")


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_public_media_prefix_is_served_in_production(client):
    scan = Credential.objects.exclude(scan="").first()
    response = client.get(scan.scan.url)
    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_lead_files_are_not_public(client, lead_with_file):
    assert lead_with_file.attachment.name.startswith("leads/")
    assert client.get(f"/media/{lead_with_file.attachment.name}").status_code == 404


@pytest.mark.django_db
def test_public_media_rejects_traversal_into_leads(client, lead_with_file):
    assert client.get(f"/media/credentials/../{lead_with_file.attachment.name}").status_code == 404


@pytest.mark.django_db
def test_lead_attachment_download_requires_staff(client, lead_with_file):
    url = f"/admin-files/lead/{lead_with_file.pk}/"
    anonymous = client.get(url)
    assert anonymous.status_code == 302 and "/admin/" in anonymous["Location"]

    staff = get_user_model().objects.create_user("xodim", password="x-parol-123", is_staff=True)
    client.force_login(staff)
    response = client.get(url)
    assert response.status_code == 200
    assert "attachment" in response["Content-Disposition"]
    assert b"".join(response.streaming_content) == b"%PDF-1.4 test"


@pytest.mark.django_db
def test_lead_attachment_download_404_without_file(admin_client):
    lead = Lead.objects.create(name="Test", phone="+998901234567")
    assert admin_client.get(f"/admin-files/lead/{lead.pk}/").status_code == 404


@pytest.mark.django_db
def test_lead_admin_shows_download_link(admin_client, lead_with_file):
    response = admin_client.get(f"/admin/api/resources/leads/{lead_with_file.pk}/")
    assert response.status_code == 200
    assert response.json()["record"]["values"]["attachment"] == f"/admin-files/lead/{lead_with_file.pk}/"


@pytest.mark.django_db
def test_oversized_body_rejected_before_csrf(client):
    response = client.post("/uz/api/lead/", {"name": "T", "phone": "+998901234567"},
                           CONTENT_LENGTH=str(settings.MAX_REQUEST_BODY_BYTES + 1),
                           HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert response.status_code == 413
    assert "juda katta" in response.content.decode()


@pytest.mark.django_db
def test_normal_body_passes_size_middleware(client, monkeypatch):
    monkeypatch.setattr("core.views.notify_telegram", lambda lead: True)
    response = client.post("/uz/api/lead/", {"name": "T", "phone": "+998901234567"},
                           HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert response.status_code == 200


def _django_setup(env_overrides):
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SECRET_KEY"}
    env.update(env_overrides)
    code = "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings'); django.setup()"
    return subprocess.run([sys.executable, "-c", code], cwd=settings.BASE_DIR, env=env,
                          capture_output=True, text=True, timeout=60)


def test_production_refuses_to_start_without_secret_key():
    result = _django_setup({"DJANGO_DEBUG": "0"})
    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr


def test_production_starts_with_build_only_secret_key():
    result = _django_setup({"DJANGO_DEBUG": "0", "DJANGO_SECRET_KEY": "build-only"})
    assert result.returncode == 0, result.stderr


def test_hsts_defaults_are_conservative_and_env_driven():
    code = ("import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings'); django.setup(); "
            "from django.conf import settings as s; "
            "print(s.SECURE_HSTS_SECONDS, s.SECURE_HSTS_INCLUDE_SUBDOMAINS, s.SECURE_HSTS_PRELOAD)")
    base = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_HSTS")}
    base.update({"DJANGO_DEBUG": "0", "DJANGO_SECRET_KEY": "test-secret"})

    def run(extra):
        return subprocess.run([sys.executable, "-c", code], cwd=settings.BASE_DIR, env={**base, **extra},
                              capture_output=True, text=True, timeout=60).stdout.split()

    assert run({}) == ["3600", "False", "False"]
    assert run({"DJANGO_HSTS_SECONDS": "31536000", "DJANGO_HSTS_INCLUDE_SUBDOMAINS": "1",
                "DJANGO_HSTS_PRELOAD": "1"}) == ["31536000", "True", "True"]


@pytest.mark.parametrize("length", ["", "abc", None])
def test_size_middleware_passes_missing_or_invalid_content_length(length):
    from django.http import HttpResponse
    from django.test import RequestFactory

    from core.middleware import MaxBodySizeMiddleware

    request = RequestFactory().post("/uz/api/lead/", data=b"", content_type="text/plain")
    if length is None:
        request.META.pop("CONTENT_LENGTH", None)
    else:
        request.META["CONTENT_LENGTH"] = length
    response = MaxBodySizeMiddleware(lambda req: HttpResponse("ok"))(request)
    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_staff_certificate_scan_is_served_in_production(client):
    certificate = StaffCertificate.objects.exclude(scan="").first()
    assert certificate.scan.url.startswith("/media/team/certificates/")
    assert client.get(certificate.scan.url).status_code == 200
