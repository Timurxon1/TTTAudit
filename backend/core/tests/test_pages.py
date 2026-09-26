import re

import pytest
from django.utils.html import escape

from core.models import TeamMember


@pytest.mark.django_db
def test_home_renders_v3_sections(client):
    response = client.get("/uz/")
    assert response.status_code == 200
    html = response.content.decode()
    assert "Qurilish auditi <em>va energiya auditi</em>" in html       # ikki asosiy yoʻnalish teng ko‘rinadi
    assert 'class="facts"' in html                                    # faktlar tasmasi
    assert "Taqqoslash vedomosti" in html and "67 285 000" in html  # vedomost namunasi
    assert html.count('data-doc-panel') == 8                          # hujjat koʻrgich
    assert 'data-react="compliance-check"' in html                    # talab tekshiruvchi
    assert "Bajarilgan ishlar reestri" in html
    assert "Koʻp soʻraladigan savollar" in html
    assert "№ 518159" in html                                         # qurilish litsenziyasi raqami
    assert "moliyaviy audit" not in html.lower()
    assert "REPER" not in html


@pytest.mark.django_db
def test_home_ru_and_en_render(client):
    assert client.get("/ru/").status_code == 200
    assert "Строительный аудит".encode() in client.get("/ru/").content
    assert client.get("/en/").status_code == 200
    assert b"Construction audit" in client.get("/en/").content


@pytest.mark.django_db
def test_root_redirects_to_uz(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response["Location"].startswith("/uz/")


@pytest.mark.django_db
def test_services_hub_lists_both_directions(client):
    html = client.get("/uz/xizmatlar/").content.decode()
    assert "Energosamaradorlik auditi" in html
    assert "Qurilishda nazorat oʻlchovi" in html
    assert html.count('data-direction="') == 2


@pytest.mark.django_db
def test_energy_direction_has_widgets_and_legal_basis(client):
    response = client.get("/uz/xizmatlar/energoaudit/")
    assert response.status_code == 200
    html = response.content.decode()
    assert 'data-react="compliance-check"' in html
    assert 'data-react="energy-estimator"' in html
    assert "ЗРУ-940" in html


@pytest.mark.django_db
def test_direction_headcount_comes_from_site_settings(client):
    from core.models import SiteSettings

    site = SiteSettings.load()
    site.staff_energy, site.staff_supervision = 31, 17
    site.save()
    energy = client.get("/uz/xizmatlar/energoaudit/").content.decode()
    construction = client.get("/uz/xizmatlar/olchov-auditi/").content.decode()
    assert "31 nafar energoaudit mutaxassisi" in energy and "24 mutaxassis" not in energy
    assert "17 nafar texnik nazorat xodimi" in construction and "16 mutaxassis" not in construction
    assert "Специалистов по энергоаудиту: 31" in client.get("/ru/xizmatlar/energoaudit/").content.decode()


@pytest.mark.django_db
def test_energy_direction_hides_unverified_bands_and_fee(client):
    html = client.get("/uz/xizmatlar/energoaudit/").content.decode()
    assert '<span class="badge">A</span>' not in html and '<span class="badge">G</span>' not in html
    assert 'data-ladder="[]"' in html
    assert "energopasport talabi hisoblanadi" in html
    assert "0,3" not in html


@pytest.mark.django_db
def test_energy_direction_shows_bands_once_verified(client, monkeypatch):
    monkeypatch.setattr("core.energy.BANDS_VERIFIED", True)
    html = client.get("/uz/xizmatlar/energoaudit/").content.decode()
    assert '<span class="badge">A</span>' in html and '<span class="badge">G</span>' in html


@pytest.mark.django_db
def test_construction_direction_lists_instruments(client):
    html = client.get("/uz/xizmatlar/olchov-auditi/").content.decode()
    assert "SNOWAY SW-M100" in html
    assert "Elektron mikrometr" in html
    assert 'data-react="energy-estimator"' not in html


@pytest.mark.django_db
def test_service_page_and_404(client):
    response = client.get("/uz/xizmatlar/olchov-auditi/nazorat-olchovi/")
    assert response.status_code == 200
    assert "Nazorat oʻlchovi".encode() in response.content
    assert client.get("/uz/xizmatlar/olchov-auditi/yoq-xizmat/").status_code == 404


@pytest.mark.django_db
def test_registry_paginates_and_filters(client):
    html = client.get("/uz/reestr/").content.decode()
    assert "143" in html                                   # jami soni sarlavhada
    assert html.count("<tr>") == 26                         # 1 sarlavha + 25 qator
    assert 'class="pager"' in html                          # sahifalash bloki
    assert '<span aria-current="page">1</span>' in html     # joriy sahifa pagerda
    assert "?page=2" in html                                 # keyingi sahifaga havola

    energy = client.get("/uz/reestr/?d=energoaudit").content.decode()
    assert "Topildi: 48 ta" in energy
    assert '<td class="tbl__dir">Qurilishda nazorat oʻlchovi</td>' not in energy
    assert '<td class="tbl__dir">Energosamaradorlik auditi</td>' in energy

    year = client.get("/uz/reestr/?y=2023").content.decode()
    assert "Topildi: 20 ta" in year

    search = client.get("/uz/reestr/?q=AGROBANK").content.decode()
    assert "AGROBANK" in search and "Topildi: 1 ta" in search

    assert client.get("/uz/reestr/?page=999").status_code == 200   # oxirgi sahifaga tushadi

    assert "Tozalash" not in client.get("/uz/reestr/?y=abc").content.decode()


@pytest.mark.django_db
def test_credentials_page_shows_all_eight_documents_with_scans(client):
    html = client.get("/uz/hujjatlar/").content.decode()
    assert html.count('class="dview"') == 8
    assert " hidden>" not in html                           # JS'siz sahifada hamma hujjat koʻrinadi
    assert "data-lightbox" in html
    assert "№ 518159" in html and "ISO 9001:2015" in html and "Imkon" in html
    assert "АФ № 00773" not in html                       # Moliya vazirligi litsenziyasi — yoʻq


@pytest.mark.django_db
def test_instruments_page_table(client):
    html = client.get("/uz/tashkilot/asboblar/").content.decode()
    assert html.count("<tr>") == 6                          # sarlavha + 5 asbob
    assert "Milliy Metrologiya" in html


@pytest.mark.django_db
def test_legislation_shows_only_verified_acts(client):
    html = client.get("/uz/qonunchilik/").content.decode()
    assert "ЗРУ-940" in html and "lex.uz" in html
    assert "A–G toifalari" not in html                     # verified_on=None — koʻrinmaydi


@pytest.mark.django_db
def test_news_list_and_detail(client):
    html = client.get("/uz/yangiliklar/").content.decode()
    assert "energoaudit-kimga-majburiy" in html
    detail = client.get("/uz/yangiliklar/energoaudit-kimga-majburiy/")
    assert detail.status_code == 200
    assert client.get("/uz/yangiliklar/yoq-maqola/").status_code == 404


@pytest.mark.django_db
def test_company_page(client):
    html = client.get("/uz/tashkilot/").content.decode()
    assert "1997" in html and "UZACE" in html and "ISO 27001" in html
    assert "Botirov" in html
    assert "filial" not in html.lower()
    assert "Buyurtmachilar orasida" not in html          # eski saytdan — mijoz tasdiqlaguncha yoʻq


@pytest.mark.django_db
def test_team_page_groups_by_department(client):
    html = client.get("/uz/jamoa/").content.decode()
    assert "<h1>Jamoa</h1>" in html and "Rahbariyat</h2>" in html and "Mutaxassislar</h2>" in html
    assert html.count('class="pm"') == 39               # direktor + 38 mutaxassis (takror birlashtirilgan)
    assert "Jami 50 xodim: 24 energoaudit, 16 texnik nazorat." in html
    assert "Energoaudit" in html and "Qurilishda nazorat oʻlchovi" in html
    assert 'aria-current="page">Jamoa</a>' in html     # menyuda «Jamoa» faol
    assert "core/img/director.jpg" not in html and 'data-person="director"' not in html
    # "== 1" emas: fotosurati bor har bir xodim nomi img alt'da HAM <b> ichida
    # takrorlanadi (bitta karta ichida 2 marta) — shu sababli karta sonini
    # <b> yorlig'i orqali sanaymiz: bitta kishi = bitta karta = bitta <b>.
    assert html.count("<b>Xudayberdiev Otabek Talipovich</b>") == 1


@pytest.mark.django_db
def test_requisites_page(client):
    html = client.get("/uz/tashkilot/rekvizitlar/").content.decode()
    assert "202216926" in html and "«TTTaudit» MChJ" in html
    assert "filial" not in html.lower()
    assert "Avisozlar" not in html                          # spec 3-qoida: Toshkent ofisi faqat aloqa sahifasida


@pytest.mark.django_db
def test_contact_and_request_pages(client):
    contact = client.get("/uz/aloqa/").content.decode()
    assert "Yangiobod" in contact and 'data-react="lead-form"' in contact
    assert "Avisozlar" not in contact and "filial" not in contact.lower()   # filiallar saytda yoʻq
    request_page = client.get("/uz/murojaat/").content.decode()
    assert 'name="csrfmiddlewaretoken"' in request_page and 'enctype="multipart/form-data"' in request_page
    sent = client.get("/uz/murojaat/?sent=1").content.decode()
    assert "Murojaat qabul qilindi. Muhandis siz bilan bogʻlanadi." in sent
    assert "ish kuni" not in sent and "bepul" not in sent


def _cards(html, marker):
    start = html.index(marker)
    section = html[start:html.index("</section>", start)]
    return re.findall(r'<a class="pm" href="/uz/jamoa/([^/]+)/"', section)


@pytest.mark.django_db
def test_team_leadership_starts_with_director_and_links_profiles(client):
    html = client.get("/uz/jamoa/").content.decode()
    leaders = _cards(html, 'id="rahbariyat"')
    assert leaders[0] == "botirov-mahammad-hoshimovich"
    assert len(leaders) == TeamMember.objects.filter(is_leadership=True).count() == 3
    assert "6 ta sertifikat" in html                                   # Xudayberdiev kartasi
    assert "Сертификатов: 6" in client.get("/ru/jamoa/").content.decode()


@pytest.mark.django_db
def test_team_specialist_tabs_filter_without_js(client):
    all_cards = _cards(client.get("/uz/jamoa/").content.decode(), 'id="mutaxassislar"')
    assert len(all_cards) == TeamMember.objects.filter(is_leadership=False).count() == 36
    html = client.get("/uz/jamoa/?bolim=construction").content.decode()
    cards = _cards(html, 'id="mutaxassislar"')
    expected = TeamMember.objects.filter(is_leadership=False, dept="construction")
    assert cards == list(expected.values_list("slug", flat=True)) and 0 < len(cards) < len(all_cards)
    assert re.search(r'href="\?bolim=construction#mutaxassislar" aria-current="page">Qurilishda nazorat oʻlchovi', html)
    assert f'Barchasi <span class="num">({len(all_cards)})</span>' in html
    assert _cards(client.get("/uz/jamoa/?bolim=nimadir").content.decode(), 'id="mutaxassislar"') == all_cards


@pytest.mark.django_db
def test_old_team_url_redirects_permanently_in_same_language(client):
    for lang in ("uz", "ru"):
        response = client.get(f"/{lang}/tashkilot/mutaxassislar/")
        assert response.status_code == 301 and response["Location"] == f"/{lang}/jamoa/"


@pytest.mark.django_db
def test_profile_with_certificates_shows_titles_and_numbers(client):
    member = TeamMember.objects.get(full_name="Xudayberdiev Otabek Talipovich")
    html = client.get(f"/uz/jamoa/{member.slug}/").content.decode()
    assert f"<title>{member.full_name} — Jamoa — TTT Audit</title>" in html
    assert "Sertifikatlar</h2>" in html and html.count('<article class="cert">') == 6
    for cert in member.certificates.all():
        assert str(escape(cert.title)) in html and str(escape(cert.number)) in html
    assert "data-lightbox" in html and "/media/team/certificates/" in html
    assert 'aria-current="page">Jamoa</a>' in html
    assert '<li><a href="/uz/jamoa/">Jamoa</a></li>' in html            # crumbs: Jamoa › ism


@pytest.mark.django_db
def test_profile_without_certificates_has_no_certificate_section(client):
    member = TeamMember.objects.filter(certificates__isnull=True, is_leadership=False).first()
    html = client.get(f"/uz/jamoa/{member.slug}/").content.decode()
    assert "Sertifikatlar</h2>" not in html and '<article class="cert">' not in html
    assert str(escape(member.full_name)) in html and "← Butun jamoa" in html


@pytest.mark.django_db
def test_director_profile_shows_education_and_experience(client):
    html = client.get("/uz/jamoa/botirov-mahammad-hoshimovich/").content.decode()
    assert "Maʼlumoti</h2>" in html and "Ish tajribasi</h2>" in html
    assert '<span class="num">1979–1989</span>' in html and "«Barkamol» AJ — bosh muhandis" in html
    assert 'alt="Botirov Mahammad Hoshimovich"' in html
    assert 'rel="prev"' not in html and 'rel="next"' in html
    assert "auditor" not in html.lower()


@pytest.mark.django_db
def test_profile_headings_translated(client):
    ru = client.get("/ru/jamoa/botirov-mahammad-hoshimovich/").content.decode()
    assert "Образование</h2>" in ru and "Опыт работы</h2>" in ru and "Ботиров Махаммад Хошимович" in ru
    member = TeamMember.objects.filter(certificates__isnull=False).distinct().first()
    en = client.get(f"/en/jamoa/{member.slug}/").content.decode()
    assert "Certificates</h2>" in en and "Issued:" in en and "— Team — TTT Audit</title>" in en


@pytest.mark.django_db
def test_unknown_profile_slug_is_404(client):
    assert client.get("/uz/jamoa/bunday-xodim-yoq/").status_code == 404
