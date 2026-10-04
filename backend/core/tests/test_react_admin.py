import pytest
from django.contrib.auth import get_user_model

from core.models import SiteText, Stat


@pytest.fixture
def react_admin_user(db):
    return get_user_model().objects.create_superuser("panel", "panel@example.uz", "panel-password")


@pytest.mark.django_db
def test_react_admin_shell_replaces_django_admin(client):
    response = client.get("/admin/")
    assert response.status_code == 200
    html = response.content.decode()
    assert 'id="admin-root"' in html
    assert "admin/admin.js" in html and "admin/admin.css" in html
    assert client.get("/admin/core/sitesettings/").status_code == 404


@pytest.mark.django_db
def test_react_admin_login_and_catalog(client, react_admin_user):
    session = client.get("/admin/api/session/").json()
    assert session["authenticated"] is False and session["csrf"]
    login = client.post("/admin/api/login/", {"username": "panel", "password": "panel-password"})
    assert login.status_code == 200 and login.json()["authenticated"] is True
    catalog = client.get("/admin/api/catalog/")
    assert catalog.status_code == 200
    assert {item["key"] for item in catalog.json()["items"]} >= {"settings", "texts", "projects", "leads"}


@pytest.mark.django_db
def test_react_admin_crud_and_anonymous_denial(client, react_admin_user):
    assert client.get("/admin/api/resources/stats/").status_code == 401
    client.force_login(react_admin_user)
    created = client.post("/admin/api/resources/stats/", {
        "value": "25", "label_uz": "Yillik tajriba", "label_ru": "", "label_en": "",
        "highlight": "on", "order": "50",
    })
    assert created.status_code == 201, created.content
    pk = created.json()["record"]["id"]
    assert Stat.objects.get(pk=pk).label_uz == "Yillik tajriba"

    updated = client.post(f"/admin/api/resources/stats/{pk}/", {
        "value": "26", "label_uz": "Yillik tajriba", "label_ru": "", "label_en": "",
        "highlight": "", "order": "50",
    })
    assert updated.status_code == 200, updated.content
    assert Stat.objects.get(pk=pk).value == "26"
    assert client.delete(f"/admin/api/resources/stats/{pk}/").status_code == 200
    assert not Stat.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_site_text_record_uses_readable_uzbek_label(client, react_admin_user):
    row = SiteText.objects.create(kind=SiteText.KIND_WIDGET, key="lf.urgent")
    client.force_login(react_admin_user)

    payload = client.get("/admin/api/resources/texts/?q=lf.urgent").json()["records"]

    assert payload == [{
        "id": row.pk,
        "label": "Shoshilinch",
        "hint": "lf.urgent",
        "values": {"text_uz": "", "text_ru": "", "text_en": ""},
    }]
