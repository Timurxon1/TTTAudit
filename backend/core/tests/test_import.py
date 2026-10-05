import json
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command
from django.test import override_settings

from core.models import (
    Branch, Client, Credential, Direction, Instrument, Project, Service,
    SiteSettings, StaffCertificate, Stat, TeamMember,
)

DATA = Path(settings.BASE_DIR) / "data" / "tttaudit"


@pytest.fixture
def own_media(tmp_path):
    """--force eski fayllarni oʻchiradi: sessiya media papkasiga tegmasligi uchun alohida MEDIA_ROOT."""
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        yield tmp_path


@pytest.mark.django_db
def test_seed_content_creates_two_directions_and_eight_services():
    assert set(Direction.objects.values_list("slug", flat=True)) == {"energoaudit", "olchov-auditi"}
    assert Service.objects.count() == 8
    assert not Service.objects.filter(slug__in=["msfo", "konsalting", "malaka-oshirish"]).exists()


@pytest.mark.django_db
def test_import_loads_client_facts():
    site = SiteSettings.load()
    assert site.tin == "202216926"
    assert (site.phone, site.phone_second) == ("+998 91 109 35 35", "+998 50 722 77 21")
    assert site.director_uz.startswith("Botirov")
    assert site.seo_title_uz == "Energoaudit va qurilishda nazorat oʻlchovi — TTT Audit, Fargʻona"
    assert Branch.objects.count() == 1                           # faqat bosh ofis
    assert Branch.objects.get().is_head_office
    assert site.office_tashkent_uz == ""
    assert Credential.objects.count() == 8
    assert Credential.objects.filter(kind="insurance").exists()
    assert Instrument.objects.count() == 5
    assert Stat.objects.count() == 4
    assert TeamMember.objects.count() == 37                      # direktor + 36 mutaxassis
    assert TeamMember.objects.filter(dept="energy").count() == 22
    assert TeamMember.objects.exclude(photo="").count() >= 30
    assert Project.objects.count() == 143
    assert Project.objects.filter(direction__slug="olchov-auditi").count() == 95
    assert Client.objects.count() > 0


@pytest.mark.django_db
def test_import_is_idempotent_without_force():
    before = Project.objects.count()
    call_command("import_tttaudit")
    assert Project.objects.count() == before


@pytest.mark.django_db
def test_import_force_recreates_tables_with_same_counts(own_media):
    models = (Branch, Client, Credential, Instrument, Project, Stat, TeamMember, StaffCertificate)
    before = {model.__name__: model.objects.count() for model in models}
    call_command("import_tttaudit", "--force")
    assert {model.__name__: model.objects.count() for model in models} == before
    scans = Credential.objects.exclude(scan="")
    assert scans.exists() and all(c.scan.storage.exists(c.scan.name) for c in scans)


@pytest.mark.django_db
def test_director_is_first_member_with_photo_and_engineering_history():
    director = TeamMember.objects.first()
    assert director.full_name == "Botirov Mahammad Hoshimovich" and director.full_name_ru == "Ботиров Махаммад Хошимович"
    assert director.dept == TeamMember.DEPT_MANAGEMENT and director.is_leadership and director.order == 0
    assert (director.role_uz, director.role_ru, director.role_en) == ("Bosh direktor", "Генеральный директор", "General Director")
    assert director.photo and director.photo.name.startswith("team/kZeWGs8BiqT2DLVxMvDS")
    assert [row["years"] for row in director.education] == ["2004", "1993", "1985"]
    assert len(director.experience) == 4
    history = json.dumps(director.education + director.experience, ensure_ascii=False).lower().replace("tttaudit", "")
    assert "audit" not in history and "аудит" not in history
    assert director.slug == "botirov-mahammad-hoshimovich"


@pytest.mark.django_db
def test_certificates_attached_to_members():
    entries = json.loads((DATA / "staff_certificates.json").read_text(encoding="utf-8"))["certificates"]
    active_entries = [entry for entry in entries if "xudayberdiev" not in entry["file"]]
    assert StaffCertificate.objects.count() == len(active_entries) == 40
    assert all(c.scan for c in StaffCertificate.objects.all())
    davronbek = TeamMember.objects.get(full_name="Botirov Davronbek Baxtiyorovich")
    assert davronbek.is_leadership and davronbek.role_en == "Deputy General Director"
    assert not TeamMember.objects.filter(full_name="Xudayberdiev Otabek Talipovich").exists()


@pytest.mark.django_db
def test_import_reports_attached_and_skipped_certificates(own_media, capsys):
    call_command("import_tttaudit", "--force")
    assert "Sertifikatlar: 40 biriktirildi, 6 otkazib yuborildi" in capsys.readouterr().out


@pytest.mark.django_db
def test_garbled_name_is_fixed_and_keeps_certificate():
    member = TeamMember.objects.get(full_name_ru="ТУХЛИБАЕВ УЛУҒБЕК СОЙИБОВИЧ")
    assert member.full_name == "Tuxlibayev Ulugʻbek Soyibovich" and member.slug == "tuxlibayev-ulugbek-soyibovich"
    assert member.certificates.count() == 1
    assert not TeamMember.objects.filter(full_name__contains="Ulu Oʻgʻligʻbek").exists()


@pytest.mark.django_db
def test_member_slugs_are_unique_and_ascii():
    slugs = list(TeamMember.objects.values_list("slug", flat=True))
    assert len(slugs) == len(set(slugs)) == 37
    assert all(slug.isascii() and slug == slug.lower() for slug in slugs)


@pytest.mark.django_db
def test_site_requisites_keep_admin_edits_without_force(own_media):
    site = SiteSettings.load()
    site.phone, site.staff_total = "+998 99 111 22 33", 51
    site.save()
    call_command("import_tttaudit")
    site = SiteSettings.load()
    assert (site.phone, site.staff_total) == ("+998 99 111 22 33", 51)
    call_command("import_tttaudit", "--force")
    site = SiteSettings.load()
    assert site.phone != "+998 99 111 22 33" and site.staff_total == 50


@pytest.mark.django_db
def test_site_requisites_fill_placeholder_defaults_without_force():
    SiteSettings.objects.all().delete()
    call_command("import_tttaudit")
    site = SiteSettings.load()
    assert site.tin == "202216926" and site.email != "info@example.uz" and site.director_uz.startswith("Botirov")


@pytest.mark.django_db
def test_repeated_force_keeps_media_file_count_stable(own_media):
    call_command("import_tttaudit", "--force")
    first = sorted(p.relative_to(own_media) for p in own_media.rglob("*") if p.is_file())
    call_command("import_tttaudit", "--force")
    second = sorted(p.relative_to(own_media) for p in own_media.rglob("*") if p.is_file())
    team = [p for p in second if p.parts[0] == "team"]
    assert len(team) == TeamMember.objects.exclude(photo="").count() + StaffCertificate.objects.count() == 37 + 40
    assert first == second                                                   # nomlar ham oʻzgarmaydi
    assert len([p for p in team if p.parts[1] == "certificates"]) == 40
