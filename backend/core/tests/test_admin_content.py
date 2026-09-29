"""Admin paneldan tahrirlanadigan kontent: sayt matnlari, vidjet matnlari, slaydlar, brend rasmlari."""
import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db.models import F
from django.test import override_settings

from core.admin import SiteTextForm
from core.models import Project, SiteSettings, SiteText, Slide, StaffCertificate

pytestmark = pytest.mark.django_db

TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082"
)


@pytest.fixture
def site_texts():
    call_command("sync_site_content")


@pytest.fixture
def staff(django_user_model):
    return django_user_model.objects.create_superuser("admin", "admin@example.uz", "parol-123-XYZ")


def _override(key, kind=SiteText.KIND_UI, **texts):
    row = SiteText.objects.get(kind=kind, key=key)
    for lang, value in texts.items():
        setattr(row, f"text_{lang}", value)
    row.save()
    return row


def test_sync_creates_every_ui_and_widget_text_once(site_texts):
    total = SiteText.objects.count()
    assert SiteText.objects.filter(kind=SiteText.KIND_UI, key="Murojaat yuborish").exists()
    assert SiteText.objects.filter(kind=SiteText.KIND_WIDGET, key="common.back").exists()
    call_command("sync_site_content")
    assert SiteText.objects.count() == total


def test_sync_keeps_admin_edits_and_removes_untouched_stale_keys(site_texts):
    _override("Murojaat yuborish", ru="Свой текст")
    SiteText.objects.create(key="eski-kalit")
    SiteText.objects.create(key="eski-tahrirlangan", text_uz="saqlansin")
    call_command("sync_site_content")
    assert SiteText.objects.get(key="Murojaat yuborish").text_ru == "Свой текст"
    assert not SiteText.objects.filter(key="eski-kalit").exists()
    assert SiteText.objects.filter(key="eski-tahrirlangan").exists()


def test_ui_override_applies_only_to_its_language(client, site_texts):
    _override("Murojaat yuborish", ru="ОСОБАЯ ЗАЯВКА")
    assert "ОСОБАЯ ЗАЯВКА" in client.get("/ru/").content.decode()
    uz = client.get("/uz/").content.decode()
    assert "Murojaat yuborish" in uz and "ОСОБАЯ ЗАЯВКА" not in uz


def test_clearing_override_restores_default_translation(client, site_texts):
    row = _override("Murojaat yuborish", en="CUSTOM REQUEST")
    assert "CUSTOM REQUEST" in client.get("/en/").content.decode()
    row.text_en = ""
    row.save()
    assert "CUSTOM REQUEST" not in client.get("/en/").content.decode()


def test_blocktranslate_override_keeps_placeholders(client, site_texts):
    _override("%(n)s yillik tajriba", uz="%(n)s yil ishonchli tajriba")
    assert "yil ishonchli tajriba" in client.get("/uz/").content.decode()


def test_widget_override_is_injected_as_json(client, site_texts):
    _override("common.back", kind=SiteText.KIND_WIDGET, en="Go back")
    body = client.get("/en/murojaat/").content.decode()
    payload = body.split('<script id="site-texts" type="application/json">')[1].split("</script>")[0]
    assert json.loads(payload) == {"common.back": "Go back"}
    assert 'id="site-texts"' not in client.get("/ru/murojaat/").content.decode()


@pytest.mark.parametrize(("key", "value", "ok"), [
    ("%(n)s yillik tajriba", "%(n)s yil", True),
    ("%(n)s yillik tajriba", "tajriba", False),
    ("%(n)s yillik tajriba", "%(n)s yil, 100% ishonch", False),
    ("%(n)s yillik tajriba", "%(n)s yil, 100%% ishonch", True),
    ("Murojaat yuborish", "Yuborish", True),
    ("Fayl hajmi %(mb)d MB dan oshmasligi kerak.", "Fayl %(size)d MB dan katta", False),
    ("Fayl hajmi %(mb)d MB dan oshmasligi kerak.", "Fayl %(mb)d MB dan katta boʻlmasin", True),
])
def test_site_text_form_validates_placeholders(site_texts, key, value, ok):
    row = SiteText.objects.get(kind=SiteText.KIND_UI, key=key)
    form = SiteTextForm(data={"text_uz": value, "text_ru": "", "text_en": ""}, instance=row)
    assert form.is_valid() is ok, form.errors


def test_widget_text_form_validates_js_placeholders(site_texts):
    row = SiteText.objects.filter(kind=SiteText.KIND_WIDGET).first()
    form = SiteTextForm(data={"text_uz": "{yangi} matn", "text_ru": "", "text_en": ""}, instance=row)
    assert not form.is_valid()


def test_site_text_admin_pages_render(client, staff, site_texts):
    client.force_login(staff)
    row = SiteText.objects.get(key="Murojaat yuborish")
    listing = client.get("/admin/api/resources/texts/?q=Murojaat")
    assert listing.status_code == 200
    assert any(item["id"] == row.pk for item in listing.json()["records"])
    detail = client.get(f"/admin/api/resources/texts/{row.pk}/")
    assert detail.status_code == 200
    assert detail.json()["record"]["values"]["text_ru"] == ""


@pytest.mark.parametrize("url", [
    "/admin/api/resources/slides/", "/admin/api/resources/settings/",
    "/admin/api/resources/staff-certificates/",
])
def test_content_admin_lists_render(client, staff, site_texts, url):
    client.force_login(staff)
    assert client.get(url).status_code == 200


def test_slides_are_seeded_and_rendered_from_admin(client, site_texts):
    assert Slide.objects.count() == 6
    first = Slide.objects.first()
    first.text_ru = "Новая подпись слайда"
    first.save()
    Slide.objects.filter(order=1).update(is_active=False)
    body = client.get("/ru/").content.decode()
    assert "Новая подпись слайда" in body
    assert body.count("data-slide>") == 5
    assert "/ 05</span>" in body


def test_branding_uploads_replace_static_logo(client):
    site = SiteSettings.load()
    site.logo_mark = SimpleUploadedFile("logo.png", TINY_PNG, content_type="image/png")
    site.og_image = SimpleUploadedFile("og.png", TINY_PNG, content_type="image/png")
    site.save()
    try:
        body = client.get("/uz/").content.decode()
        assert "/media/branding/logo" in body and "/media/branding/og" in body
        response = client.get(site.logo_mark.url)
        response.close()  # FileResponse faylni yopsin (Windows'da ochiq fayl oʻchirilmaydi)
        assert response.status_code == 200
    finally:
        site.logo_mark.delete(save=False)
        site.og_image.delete(save=False)
        site.save()


def test_staff_certificate_title_and_issuer_are_translated(client):
    assert not StaffCertificate.objects.filter(title_ru="").exists()
    # Asl nomi inglizcha boʻlmagan (tarjimasi farq qiladigan) sertifikat
    cert = StaffCertificate.objects.exclude(issuer_en="").exclude(title_en=F("title")).first()
    body = client.get(f"/en/jamoa/{cert.member.slug}/").content.decode()
    assert cert.title_en in body and cert.issuer_en in body


def test_every_project_has_english_title():
    assert not Project.objects.filter(title_en="").exists()


@override_settings(ALLOWED_HOSTS=["healthcheck.railway.app"])
def test_healthz_answers_platform_healthcheck(client):
    response = client.get("/healthz", HTTP_HOST="healthcheck.railway.app")
    assert response.status_code == 200 and response.content == b"ok"
