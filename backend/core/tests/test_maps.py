import json
import re
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import translation

from core import maps
from core.geo.projection import project
from core.geo.regions import REGIONS, region_name, uzmap
from core.management.commands.import_tttaudit import Command as ImportCommand
from core.models import Project, ProjectLocation

# bmmaudit.uz tools/mkmap.py: shahar (lon, lat) va uzmap.js dagi holst nuqtasi
MKMAP_CITIES = {
    "fargona": (71.784, 40.389),
    "samarqand": (66.959, 39.654),
    "urganch": (60.633, 41.550),
}


def test_projection_reproduces_uzmap_city_points():
    cities = uzmap()["cities"]
    for key, (lon, lat) in MKMAP_CITIES.items():
        x, y = project(lat, lon)
        assert abs(x - cities[key][0]) <= 0.2 and abs(y - cities[key][1]) <= 0.2, key


def test_uzmap_has_all_region_keys_and_names():
    assert {r["key"] for r in uzmap()["regions"]} == set(REGIONS)
    assert region_name("fargona", "ru") == "Ферганская область"
    assert region_name("toshkent_shahri", "en") == "Tashkent City"
    assert region_name("nomalum") == "nomalum"


@pytest.mark.django_db
def test_import_loads_locations_high_public_medium_hidden_none_skipped():
    high = ProjectLocation.objects.filter(confidence="high")
    medium = ProjectLocation.objects.filter(confidence="medium")
    assert high.exists() and not high.filter(is_public=False).exists()
    assert medium.count() == 4 and not medium.filter(is_public=True).exists()
    assert not ProjectLocation.objects.filter(project__order=8).exists()          # confidence none
    oxygen = ProjectLocation.objects.get(project__order=48)                        # nomidagi TASHKENT — dalil emas
    assert oxygen.confidence == "medium" and not oxygen.is_public
    assert set(Project.objects.filter(abroad=True).values_list("order", flat=True)) == {75, 88}
    assert ProjectLocation.objects.filter(project__order=5).count() == 2           # ikki hudud
    region_only = ProjectLocation.objects.get(project__order=100)
    assert region_only.lat is None and region_only.lon is None
    fergana = ProjectLocation.objects.filter(city_uz="Fargʻona").first()
    assert (fergana.city_ru, fergana.city_en) == ("Фергана", "Fergana")
    assert ProjectLocation.objects.filter(city_uz="Muborak").first().city_en == "Muborak"


@pytest.mark.django_db
def test_import_locations_idempotent_and_force_recreates(tmp_path, settings):
    before = ProjectLocation.objects.count()
    call_command("import_tttaudit", stdout=StringIO())
    assert ProjectLocation.objects.count() == before
    settings.MEDIA_ROOT = str(tmp_path)
    call_command("import_tttaudit", "--force", stdout=StringIO())
    assert ProjectLocation.objects.count() == before


@pytest.mark.django_db
def test_import_skips_unknown_region_with_ascii_count():
    ProjectLocation.objects.all().delete()
    out = StringIO()
    command = ImportCommand(stdout=out)
    command._locations([
        {"order": 1, "confidence": "high", "abroad": False,
         "locations": [{"region": "atlantida", "city_uz": "X", "lat": 1, "lon": 1},
                       {"region": "buxoro", "city_uz": "Buxoro", "city_ru": "Бухара", "lat": 39.77, "lon": 64.42}]},
        {"order": 9999, "confidence": "high", "abroad": False, "locations": []},
    ])
    assert list(ProjectLocation.objects.values_list("region", "city_en")) == [("buxoro", "Bukhara")]
    message = out.getvalue()
    assert "nomalum hudud 1" in message and "nomalum loyiha 1" in message and message.isascii()


@pytest.mark.django_db
def test_map_context_counts_regions_markers_and_region_only():
    with translation.override("uz"):
        ctx = maps.projects_map_context(Project.objects.all())
    public = ProjectLocation.objects.filter(is_public=True, project__abroad=False)
    assert ctx["totals"]["projects"] == public.values("project").distinct().count()
    regions = {r["key"]: r for r in ctx["regions"]}
    assert len(regions) == 14
    assert regions["fargona"]["count"] == public.filter(region="fargona").values("project").distinct().count()
    assert regions["fargona"]["level"] == 3 and regions["qoraqalpogiston"]["level"] == 1
    # Qoraqalpogʻistondagi ish faqat hudud nomi bilan: boʻyoqda bor, belgi yoʻq
    assert regions["qoraqalpogiston"]["count"] >= 1
    assert not [m for m in ctx["markers"] if m["region"] == "qoraqalpogiston"]
    fergana = next(m for m in ctx["markers"] if m["key"] == "fargona:Fargʻona")
    assert fergana["count"] == public.filter(city_uz="Fargʻona").values("project").distinct().count()
    assert fergana["label"] and 900 < fergana["x"] < 930
    assert ctx["off_map"] == Project.objects.count() - ctx["totals"]["projects"]
    merged = [m for m in ctx["markers"] if ", " in m["name"]]
    assert [m["name"] for m in merged] == ["Chimyon, Burchmulla"]
    assert ctx["totals"]["cities"] == public.exclude(lat=None).values("city_uz").distinct().count()


@pytest.mark.django_db
def test_map_context_dept_filter():
    all_ctx = maps.projects_map_context(Project.objects.all())
    energy = maps.projects_map_context(Project.objects.all(), dept="energy")
    construction = maps.projects_map_context(Project.objects.all(), dept="construction")
    assert energy["totals"]["projects"] + construction["totals"]["projects"] == all_ctx["totals"]["projects"]
    assert energy["totals"]["projects"] == all_ctx["totals"]["energy"]
    assert [t["key"] for t in energy["tabs"] if t["active"]] == ["energy"]
    assert maps.projects_map_context(Project.objects.all(), dept="bad")["dept"] == ""
    hidden = [m for m in construction["markers"] if m["hidden"]]
    assert all(m["count"] == 0 for m in hidden)
    assert energy["off_map"] == Project.objects.filter(direction__slug="energoaudit").count() - energy["totals"]["projects"]


def _section(html, marker, end="</section>"):
    start = html.index(marker)
    return html[start:html.index(end, start)]


def _visible_markers(html):
    return len(re.findall(r'<a class="geo__mk" ', html))


@pytest.mark.django_db
def test_home_renders_map_instead_of_table(client):
    html = client.get("/uz/").content.decode()
    section = _section(html, 'id="loyihalar"')
    assert "Bajarilgan ishlar reestri" in section and "143 ta bajarilgan ish" in section
    assert "Toʻliq reestr" in section
    assert "<table" not in section
    assert section.count('<path d="') + section.count('<path class="geo__rg"') == 28   # kontur + 14 hudud
    ctx = maps.projects_map_context(Project.objects.all())
    assert _visible_markers(section) == sum(1 for m in ctx["markers"] if not m["hidden"])
    assert f'data-stat="projects">{ctx["totals"]["projects"]}<' in section
    assert f'data-stat="cities">{ctx["totals"]["cities"]}<' in section
    assert "Qayerlarda ishlaganmiz" in section and "Xaritada loyiha" in section
    data = json.loads(re.search(r'<script id="uzmap-data" type="application/json">(.*?)</script>', html, re.S).group(1))
    assert len(data["projects"]) == ctx["totals"]["projects"] and data["live"] is True
    assert set(data["regions"]) <= set(REGIONS)


@pytest.mark.django_db
def test_home_map_dept_param_filters_without_js(client):
    html = client.get("/uz/?yo=construction").content.decode()
    ctx = maps.projects_map_context(Project.objects.all(), dept="construction")
    assert _visible_markers(html) == sum(1 for m in ctx["markers"] if not m["hidden"])
    assert f'data-stat="projects">{ctx["totals"]["projects"]}<' in html
    assert 'href="?yo=construction#xarita" data-dept="construction" aria-current="true"' in html
    assert "Где мы работали" in client.get("/ru/").content.decode()
    assert "Where we have worked" in client.get("/en/").content.decode()


@pytest.mark.django_db
def test_registry_region_filter_and_map(client):
    html = client.get("/uz/reestr/").content.decode()
    assert 'id="xarita"' in html and '<select class="select" id="f-h" name="hudud">' in html
    fergana = client.get("/uz/reestr/?hudud=fargona").content.decode()
    expected = Project.objects.filter(locations__region="fargona", locations__is_public=True).distinct().count()
    assert f"Topildi: {expected} ta" in fergana
    assert '<option value="fargona" selected>' in fergana
    assert 'class="geo__rg is-sel" href="/uz/reestr/?hudud=fargona#xarita"' in fergana
    assert "Tozalash" in fergana
    bad = client.get("/uz/reestr/?hudud=atlantida").content.decode()
    assert "Topildi: 143 ta" in bad and "Tozalash" not in bad
    tabs = client.get("/uz/reestr/?hudud=fargona&d=energoaudit").content.decode()
    assert 'data-dept="energy" aria-current="true"' in tabs
    assert '"live": false' in tabs
    assert "Bukhara Region" in client.get("/en/reestr/").content.decode()


@pytest.mark.django_db
def test_hidden_medium_location_does_not_filter_registry(client):
    oxygen = ProjectLocation.objects.get(project__order=48)
    assert oxygen.region == "toshkent_shahri"
    html = client.get("/uz/reestr/?hudud=toshkent_shahri&q=OXYGEN").content.decode()
    assert "Topildi: 0 ta" in html
    oxygen.is_public = True
    oxygen.save()
    html = client.get("/uz/reestr/?hudud=toshkent_shahri&q=OXYGEN").content.decode()
    assert "Topildi: 1 ta" in html
