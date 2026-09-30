import pytest
from django.utils import translation

from core import compliance, energy
from core.models import Direction, SiteSettings, TeamMember, member_slug


@pytest.mark.django_db
def test_tr_falls_back_to_uz_when_translation_empty():
    d = Direction.objects.create(slug="tr-fallback-check", title_uz="Energoaudit", title_ru="", summary_uz="x")
    with translation.override("ru"):
        assert d.tr("title") == "Energoaudit"
    d.title_ru = "Энергоаудит"
    with translation.override("ru"):
        assert d.tr("title") == "Энергоаудит"


@pytest.mark.django_db
def test_site_settings_load_creates_single_row():
    # seed_content/import_tttaudit already create the singleton for the test session;
    # delete it here (inside this test's transaction, so it doesn't leak to other
    # tests) to exercise the "creates the row when the table is empty" branch.
    SiteSettings.objects.all().delete()
    assert SiteSettings.objects.count() == 0
    site = SiteSettings.load()
    assert site.org_name_uz == "«TTTaudit» MChJ"
    assert SiteSettings.load().pk == site.pk


def test_energy_category_bands():
    assert energy.category_for(30) == "A"
    assert energy.category_for(100) == "D"
    assert energy.category_for(500) == "G"
    assert energy.category_for(None) is None


def test_compliance_registry_threshold_triggers_mandatory_audit():
    result = compliance.evaluate(object_kind="industrial", annual_kwh=5_000_000)
    assert "mandatory_energy_audit" in [r.key for r in result.requirements]


def test_compliance_budget_construction_has_no_unverified_fee_cap():
    result = compliance.evaluate(object_kind="construction", funding="budget", estimate_value="1000000")
    assert result.estimated_fee is None
    assert [r.key for r in result.requirements] == ["control_measurement"]
    with translation.override("uz"):
        assert "0,3" not in str(result.requirements[0].note)


def test_member_slug_drops_okina_and_apostrophes():
    assert member_slug("Joʻraev Jasur Alisher Oʻgʻli") == "joraev-jasur-alisher-ogli"
    assert member_slug("Boltaboev Doniyorjon Neʼmatillo") == "boltaboev-doniyorjon-nematillo"
    assert member_slug("") == "xodim"


@pytest.mark.django_db
def test_member_slug_is_unique_on_name_collision():
    first = TeamMember.objects.create(full_name="Test Xodim Oʻgʻli", role_uz="Muhandis", order=90)
    second = TeamMember.objects.create(full_name="Test Xodim O'g'li", role_uz="Muhandis", order=91)
    assert (first.slug, second.slug) == ("test-xodim-ogli", "test-xodim-ogli-2")
    with translation.override("uz"):
        assert second.get_absolute_url() == "/uz/jamoa/test-xodim-ogli-2/"


def test_member_timeline_uses_language_and_skips_bad_rows():
    member = TeamMember(education=[
        "eski satr",
        {"years": {"uz": "1997 — hozirgacha", "en": "1997 — present"}, "uz": "Direktor", "en": "Director"},
        {"years": "2004", "uz": "Institut"},
        {"years": "2005", "uz": ""},
    ])
    with translation.override("en"):
        assert member.education_rows() == [
            {"years": "1997 — present", "text": "Director"}, {"years": "2004", "text": "Institut"},
        ]
    with translation.override("ru"):
        assert member.education_rows()[0] == {"years": "1997 — hozirgacha", "text": "Direktor"}


@pytest.mark.django_db
def test_new_team_portraits_are_not_zoomed_like_legacy_bulletin_photos():
    member = TeamMember.objects.create(
        full_name="Yangi Portret",
        slug="yangi-portret",
        role_uz="Mutaxassis",
        dept=TeamMember.DEPT_ENERGY,
        photo="team/photo_2026-09-30_09-42-20.jpg",
    )
    assert member.photo_has_band is False

    member.photo = "team/legacy-bulletin.jpg"
    assert member.photo_has_band is True


@pytest.mark.django_db
def test_migration_fills_unique_slugs_for_existing_members():
    import importlib

    from django.apps import apps

    migration = importlib.import_module("core.migrations.0002_team_profiles_certificates")
    TeamMember.objects.create(full_name="Ikki Xodim", role_uz="x", slug="vaqtincha-1", order=95)
    TeamMember.objects.create(full_name="Ikki Xodim", role_uz="x", slug="vaqtincha-2", order=96)
    migration.fill_slugs(apps, None)
    slugs = list(TeamMember.objects.values_list("slug", flat=True))
    assert len(slugs) == len(set(slugs))
    assert {"ikki-xodim", "ikki-xodim-2"} <= set(slugs)
