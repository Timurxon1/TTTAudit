from pathlib import Path

from django.conf import settings

DIST = Path(settings.BASE_DIR) / "frontend" / "dist" / "widgets"


def test_widget_bundle_is_built():
    assert (DIST / "widgets.js").exists(), "cd frontend && npm run build"
    assert (DIST / "style.css").exists()
    css = (DIST / "style.css").read_text(encoding="utf-8")
    for cls in (".check", ".est", ".form", ".reqs", ".ladder", ".field"):
        assert cls in css, cls


def test_widget_bundle_has_ru_and_en_strings():
    """React vidjetlari (ComplianceCheck/EnergyEstimator/LeadForm) ichidagi
    matnlar `frontend/src/i18n.js` orqali uch tilda — bundle uz bilan bir
    qatorda ru/en satrlarni ham o'z ichiga olishi kerak (aks holda vidjetlar
    /ru/ va /en/ sahifalarda o'zbekcha chiqib qoladi)."""
    js = (DIST / "widgets.js").read_text(encoding="utf-8")
    assert "Отправить заявку" in js  # LeadForm/ComplianceCheck submit tugmasi — ru
    assert "Send a request" in js  # LeadForm/ComplianceCheck submit tugmasi — en
    assert "Murojaat yuborish" in js  # xuddi shu tugma — uz (fallback / default til)
    assert "Soʻrov yuborish" not in js
    assert "Андижанская область" in js and "Ташкент (город)" in js


def test_widget_bundle_has_no_unsourced_claims():
    """Javob muddati, «bepul» va 0,3% chegarasi manbasiz — vidjetda ham boʻlmasligi kerak."""
    js = (DIST / "widgets.js").read_text(encoding="utf-8")
    for phrase in ("ish kuni", "bepul", "рабочего дня", "бесплатн", "business day", "free of charge", "0,3%", "0.3%"):
        assert phrase not in js, phrase
    assert "Maʼlumotlar faqat murojaatni koʻrib chiqish uchun ishlatiladi." in js   # SSR _lead.html bilan bir xil
