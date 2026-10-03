"""Mijoz faktlarini data/tttaudit/*.json dan bazaga yuklaydi.

    python manage.py import_tttaudit           # boʻsh jadvallarni toʻldiradi
    python manage.py import_tttaudit --force   # jadvallarni fayldagi holatga qaytaradi

Oldin `seed_content` ishga tushirilgan boʻlishi shart (yoʻnalishlar kerak).

Manba fayllar:
    facts.json     kompaniya rekvizitlari, hujjatlar (skan bilan), asboblar, raqamlar
    staff.json     39 qator (byulleten; takror birlashtirilgach 38 mutaxassis), suratlar img/staff/
    staff_certificates.json  46 shaxsiy sertifikat skani (img/staff_certs/), xodimga name_ru boʻyicha
    projects.json  143 loyiha (byulleten), buyurtmachi nomi bilan
    project_locations.json  loyiha joylari (ish nomi/buyurtmachi matnidan), `order` boʻyicha
    clients.json   eski saytdagi mijozlar roʻyxati (soha bilan)

Egalik qilinadigan jadvallar: Branch, Credential, Instrument, Stat, TeamMember (direktor ham),
StaffCertificate, Project, ProjectLocation, Client. --force ularni fayllari bilan qayta yaratadi — admin paneldagi
tahrirlar yoʻqoladi. SiteSettings rekvizitlari: flagsiz faqat boʻsh (yoki model standart qiymatidagi)
maydonlar toʻldiriladi, --force hammasini fayldagi qiymatga qaytaradi (matnlar seed_content'da).
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import (
    Branch, Client, Credential, Direction, Instrument, Project, ProjectLocation, SiteSettings, StaffCertificate,
    Stat, TeamMember,
)
from core.geo.regions import REGIONS

DATA_DIR = Path(settings.BASE_DIR) / "data" / "tttaudit"
DEPT_TO_DIRECTION = {"energy": "energoaudit", "construction": "olchov-auditi"}
LEADERSHIP_WORDS = ("директор", "начальник", "руководител")

# Asbob nomining umumiy (modelsiz) qismi: uz -> (ru, en). Model nomi oʻzgarmaydi.
INSTRUMENT_NAMES = {
    "Lazerli masofaoʻlchagich": ("Лазерный дальномер", "Laser distance meter"),
    "Elektron mikrometr": ("Электронный микрометр", "Electronic micrometer"),
    "Dataloger termogigrometr": ("Даталоггер-термогигрометр", "Temperature and humidity data logger"),
}
# Oʻlchov chegarasi: toʻliq matn boʻyicha mos kelmasa «X gacha, xatolik Y» shakli tahlil qilinadi
INSTRUMENT_RANGES = {
    "Harorat va namlik qaydi": ("Регистрация температуры и влажности", "Temperature and humidity logging"),
}
RANGE_PATTERN = re.compile(r"^(?:(?P<upto>.+?) gacha|(?P<span>[^,]+?)), xatolik (?P<error>.+)$")

# staff.json da lotin yozuvi (name_uz) boʻsh qatorlar: name_ru (katta harf, bitta boʻshliq) -> lotin
STAFF_LATIN_NAMES = {
    "ЗУҲРИДДИНОВ ТЕМУРЖОН ДОНИЁРЖОН ЎҒЛИ": "Zuhriddinov Temurjon Doniyorjon oʻgʻli",
    "ЭРГАШЕВ ШАВКАТ РАШИТОВИЧ": "Ergashev Shavkat Rashitovich",
}

# staff.json dagi buzilgan ismlar (fayl oʻzgartirilmaydi): asl name_ru -> (toʻgʻri ru, toʻgʻri lotin).
# Sertifikatlar asl name_ru boʻyicha moslashtiriladi.
STAFF_NAME_FIXES = {
    "ТУХЛИБАЕВ УЛУ ЎҒЛИҒБЕК СОЙИБОВИЧ": ("ТУХЛИБАЕВ УЛУҒБЕК СОЙИБОВИЧ", "Tuxlibayev Ulugʻbek Soyibovich"),
}

# Direktor staff.json da yoʻq. Tarjimai hol faqat muhandislik tarixi: eski saytdagi moliyaviy audit,
# auditorlar palatasi, oʻquv markazi va imtihon komissiyasi qatorlari chiqarilmagan — mijoz tasdiqlashi kerak.
DIRECTOR = {
    "full_name": "Botirov Mahammad Hoshimovich",
    "full_name_ru": "Ботиров Махаммад Хошимович",
    "role": ("Bosh direktor", "Генеральный директор", "General Director"),
    "photo": "img/team/kZeWGs8BiqT2DLVxMvDS.jpg",
    "education": [
        {"years": "2004",
         "uz": "Fargʻona politexnika instituti, iqtisodchi (imtiyozli diplom)",
         "ru": "Ферганский политехнический институт, экономист (диплом с отличием)",
         "en": "Fergana Polytechnic Institute, economist (diploma with honours)"},
        {"years": "1993",
         "uz": "Toshkent toʻqimachilik va yengil sanoat instituti, muhandis",
         "ru": "Ташкентский институт текстильной и лёгкой промышленности, инженер",
         "en": "Tashkent Institute of Textile and Light Industry, engineer"},
        {"years": "1985",
         "uz": "Fargʻona yengil sanoat texnikumi, texnolog (imtiyozli diplom)",
         "ru": "Ферганский техникум лёгкой промышленности, технолог (диплом с отличием)",
         "en": "Fergana College of Light Industry, technologist (diploma with honours)"},
    ],
    "experience": [
        {"years": "1979–1989",
         "uz": "Fargʻona toʻqimachilik kombinati — smena ustasi, sex boshligʻi",
         "ru": "Ферганский текстильный комбинат — сменный мастер, начальник цеха",
         "en": "Fergana Textile Mill — shift foreman, head of workshop"},
        {"years": "1989–1992",
         "uz": "Fargʻona toʻqimachilik kombinati — ishlab chiqarish direktori",
         "ru": "Ферганский текстильный комбинат — директор производства",
         "en": "Fergana Textile Mill — production director"},
        {"years": "1993–1995",
         "uz": "«Barkamol» AJ — bosh muhandis",
         "ru": "АО «Баркамол» — главный инженер",
         "en": "Barkamol JSC — chief engineer"},
        {"years": {"uz": "1997 — hozirgacha", "ru": "1997 — н. в.", "en": "1997 — present"},
         "uz": "«TTTaudit» MChJ — bosh direktor",
         "ru": "ООО «TTTaudit» — генеральный директор",
         "en": "TTTaudit LLC — General Director"},
    ],
}

# Shahar nomining inglizcha shakli; roʻyxatda boʻlmasa oʻzbekchasi ishlatiladi
CITY_EN = {
    "Fargʻona": "Fergana", "Toshkent": "Tashkent", "Buxoro": "Bukhara", "Samarqand": "Samarkand",
    "Xiva": "Khiva", "Qarshi": "Karshi", "Termiz": "Termez", "Jizzax": "Jizzakh", "Andijon": "Andijan",
    "Urganch": "Urgench", "Navoiy": "Navoi", "Guliston": "Gulistan", "Qoʻqon": "Kokand",
    "Margʻilon": "Margilan",
}

# Reyestr hujjati: facts.json dagi `number` aslida reyting — raqam VM qarori, reyting doirasiga qoʻshiladi
REGISTRY_NUMBER = "VM qarori № 673"
REGISTRY_RANKING = {
    "uz": " (10-oʻrin, reyting 14.5)",
    "ru": " (10-е место, рейтинг 14,5)",
    "en": " (10th place, rating 14.5)",
}


def load_json(name: str) -> dict:
    path = DATA_DIR / name
    if not path.exists():
        raise CommandError(f"{path} topilmadi")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_date(value: str | None) -> dt.date | None:
    return dt.date.fromisoformat(value) if value else None


def normalize_name(value: str) -> str:
    return " ".join((value or "").split()).upper()


def instrument_name(name_uz: str) -> tuple[str, str]:
    """«Lazerli masofaoʻlchagich SW-50G» -> («Лазерный дальномер SW-50G», "Laser distance meter SW-50G")."""
    for generic, (ru, en) in INSTRUMENT_NAMES.items():
        if name_uz.startswith(generic):
            model = name_uz[len(generic):]
            return ru + model, en + model
    return "", ""


def instrument_range(range_uz: str) -> tuple[str, str]:
    """«50 m gacha, xatolik ±2 mm» -> («до 50 м, погрешность ±2 мм», "up to 50 m, error ±2 mm")."""
    if range_uz in INSTRUMENT_RANGES:
        return INSTRUMENT_RANGES[range_uz]
    match = RANGE_PATTERN.match(range_uz or "")
    if not match:
        return "", ""
    error_ru, error_en = _ru_units(match["error"]), match["error"].replace(",", ".")
    if match["upto"]:
        return f"до {_ru_units(match['upto'])}, погрешность {error_ru}", f"up to {match['upto']}, error {error_en}"
    return f"{_ru_units(match['span'])}, погрешность {error_ru}", f"{match['span']}, error {error_en}"


def _ru_units(text: str) -> str:
    """Rus matnida birliklar kirillda: m -> м, mm -> мм."""
    return re.sub(r"\bmm\b", "мм", re.sub(r"\bm\b", "м", text))


def attach(field, rel_path: str | None) -> None:
    """data/tttaudit/<rel_path> faylini ImageField/FileField ga nusxalaydi.

    Maydonda avvalgi fayl boʻlsa, u oldin oʻchiriladi — media/ da yetim nusxa qolmaydi.
    """
    if not rel_path:
        return
    source = DATA_DIR / rel_path
    if not source.exists():
        raise CommandError(f"Fayl topilmadi: {source}")
    if field.name:
        field.delete(save=False)
    with source.open("rb") as handle:
        field.save(source.name, File(handle), save=False)


def delete_files(model) -> None:
    """Jadvaldagi barcha yozuvlarning FileField/ImageField fayllarini diskdan oʻchiradi."""
    names = [f.name for f in model._meta.fields if f.get_internal_type() in ("FileField", "ImageField")]
    for obj in model.objects.all():
        for name in names:
            field = getattr(obj, name)
            if field.name:
                field.delete(save=False)


class Command(BaseCommand):
    help = "data/tttaudit/*.json dagi mijoz faktlarini bazaga yuklaydi."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Jadvallarni qayta yaratish.")

    def handle(self, *args, **options):
        facts = load_json("facts.json")
        staff = load_json("staff.json")
        staff_certificates = load_json("staff_certificates.json")
        projects = load_json("projects.json")
        locations = load_json("project_locations.json")
        clients = load_json("clients.json")
        force = options["force"]

        directions = {d.slug: d for d in Direction.objects.all()}
        missing = set(DEPT_TO_DIRECTION.values()) - set(directions)
        if missing:
            raise CommandError(f"Yonalish topilmadi: {sorted(missing)}. Avval: python manage.py seed_content")

        with transaction.atomic():
            self._site(facts["company"], force)
            self._table(Branch, force, lambda: self._branches(facts["company"]))
            self._table(Credential, force, lambda: self._credentials(facts["credentials"]))
            self._table(Instrument, force, lambda: self._instruments(facts["instruments"], directions))
            self._table(Stat, force, lambda: self._stats(facts["stats"]))
            self._people(staff["staff"], staff_certificates["certificates"], force)
            self._table(Project, force, lambda: self._projects(projects["projects"], directions))
            self._table(ProjectLocation, force, lambda: self._locations(locations["projects"]))
            self._table(Client, force, lambda: self._clients(clients))

        # Konsol xabari ASCII: Windows konsoli oʻ/gʻ ni chiqara olmaydi
        self.stdout.write(self.style.SUCCESS(
            f"Yuklandi: {Branch.objects.count()} ofis / {Credential.objects.count()} hujjat / "
            f"{Instrument.objects.count()} asbob / {Stat.objects.count()} raqam / "
            f"{TeamMember.objects.count()} xodim / {StaffCertificate.objects.count()} sertifikat / "
            f"{Project.objects.count()} loyiha / {ProjectLocation.objects.count()} joy / "
            f"{Client.objects.count()} mijoz"
        ))

    def _table(self, model, force: bool, fill) -> None:
        if model.objects.exists() and not force:
            self.stdout.write(f"{model.__name__}: malumot bor - otkazib yuborildi (--force).")
            return
        delete_files(model)
        model.objects.all().delete()
        fill()

    def _people(self, staff: list[dict], certificates: list[dict], force: bool) -> None:
        """TeamMember va StaffCertificate birga: xodimlar qayta yaratilsa, sertifikatlar ham (fayllari bilan)."""
        rebuild_team = force or not TeamMember.objects.exists()
        if rebuild_team:
            self._clear(StaffCertificate)
            self._clear(TeamMember)
            self._director()
            self._team(staff)
        else:
            self.stdout.write("TeamMember: malumot bor - otkazib yuborildi (--force).")
        if StaffCertificate.objects.exists():
            self.stdout.write("StaffCertificate: malumot bor - otkazib yuborildi (--force).")
            return
        self._certificates(staff, certificates)

    @staticmethod
    def _clear(model) -> None:
        delete_files(model)
        model.objects.all().delete()

    def _site(self, company: dict, force: bool) -> None:
        """Rekvizitlar. Flagsiz faqat boʻsh yoki model standartidagi maydon toʻldiriladi — admin tahriri qoladi."""
        values = {
            "brand_name": "TTT AUDIT",
            "org_name_uz": company["legal_name_uz"],
            "org_name_ru": company["legal_name_ru"],
            "org_name_en": company["legal_name_en"],
            "tin": company["tin"],
            "founded_year": company["founded_year"],
            "experience_years": company["experience_years"],
            "staff_total": company["staff_total"],
            "staff_energy": company["staff_energy"],
            "staff_supervision": company["staff_supervision"],
            "phone": company["phone"],
            "phone_second": company["phone_second"],
            "email": company["email"],
            "director_uz": company["director"],
            "director_ru": company["director_ru"],
            "director_en": company["director"],
            "map_lat": company["map_lat"],
            "map_lng": company["map_lng"],
        }
        for lang in ("uz", "ru", "en"):
            values[f"address_{lang}"] = company[f"address_{lang}"]
        site = SiteSettings.load()
        # Filiallar saytda koʻrsatilmaydi (Timur, 2026-09-17) — eski qiymat qolmasin
        for lang in ("uz", "ru", "en"):
            setattr(site, f"office_tashkent_{lang}", "")
        for name, value in values.items():
            if force or self._is_unset(site, name):
                setattr(site, name, value)
        if force:
            # Tasdiqlanmagan qiymatlar: faqat --force da tozalanadi (standarti allaqachon boʻsh)
            site.report_turnaround_days = None
            site.work_hours_uz = site.work_hours_ru = site.work_hours_en = ""
        site.save()

    @staticmethod
    def _is_unset(site: SiteSettings, name: str) -> bool:
        """Maydon hali tahrirlanmagan: boʻsh yoki model standart qiymatida."""
        current = getattr(site, name)
        field = SiteSettings._meta.get_field(name)
        return current in (None, "") or (field.has_default() and current == field.get_default())

    def _branches(self, company: dict) -> None:
        Branch.objects.bulk_create([
            Branch(city_uz="Fargʻona", city_ru="Фергана", city_en="Fergana",
                   address_uz=company["address_uz"], address_ru=company["address_ru"],
                   address_en=company["address_en"], head=company["director"],
                   phone=company["phone"], is_head_office=True, order=0),
        ])  # Faqat bosh ofis: filiallar saytda yoʻq (Timur, 2026-09-17)

    def _credentials(self, credentials: list[dict]) -> None:
        valid = {key for key, _ in Credential.KIND_CHOICES}
        for order, c in enumerate(c for c in credentials if c.get("show")):
            if c["kind"] not in valid:
                raise CommandError(f"facts.json: nomalum hujjat turi {c['kind']!r}, ruxsat: {sorted(valid)}")
            number, scope = c["number"], {lang: c[f"scope_{lang}"] for lang in ("uz", "ru", "en")}
            if c["kind"] == "registry":
                number = REGISTRY_NUMBER
                scope = {lang: text + REGISTRY_RANKING[lang] for lang, text in scope.items()}
            obj = Credential(
                kind=c["kind"], number=number,
                issuer_uz=c["issuer_uz"], issuer_ru=c["issuer_ru"], issuer_en=c["issuer_en"],
                scope_uz=scope["uz"], scope_ru=scope["ru"], scope_en=scope["en"],
                issued_on=parse_date(c.get("issued_on")), valid_until=parse_date(c.get("valid_until")),
                show_in_hero=order < 3, order=order,
            )
            attach(obj.scan, c.get("scan"))
            obj.save()

    def _instruments(self, instruments: list[dict], directions: dict) -> None:
        construction = directions["olchov-auditi"]
        rows = []
        for order, i in enumerate(instruments):
            name_ru, name_en = instrument_name(i["name_uz"])
            range_ru, range_en = instrument_range(i.get("range_uz", ""))
            rows.append(Instrument(
                name_uz=i["name_uz"], name_ru=i.get("name_ru") or name_ru, name_en=i.get("name_en") or name_en,
                serial=i.get("serial", ""), certificate_no=i.get("cert", ""),
                verified_on=parse_date(i.get("verified_on")), valid_until=parse_date(i.get("valid_until")),
                range_uz=i.get("range_uz", ""), range_ru=range_ru, range_en=range_en,
                direction=construction, order=order,
            ))
        Instrument.objects.bulk_create(rows)

    def _stats(self, stats: list[dict]) -> None:
        Stat.objects.bulk_create([
            Stat(value=s["value"], label_uz=s["label_uz"], label_ru=s["label_ru"],
                 label_en=s["label_en"], order=order)
            for order, s in enumerate(stats)
        ])

    def _director(self) -> None:
        role_uz, role_ru, role_en = DIRECTOR["role"]
        obj = TeamMember(
            full_name=DIRECTOR["full_name"], full_name_ru=DIRECTOR["full_name_ru"],
            role_uz=role_uz, role_ru=role_ru, role_en=role_en,
            dept=TeamMember.DEPT_MANAGEMENT, is_leadership=True, order=0,
            education=DIRECTOR["education"], experience=DIRECTOR["experience"],
        )
        attach(obj.photo, DIRECTOR["photo"])
        obj.save()

    def _team(self, staff: list[dict]) -> None:
        seen_names: set[str] = set()
        skipped = 0
        for order, row in enumerate(staff, start=1):   # 0 — direktor
            latin_name = (row.get("name_uz") or "").strip()
            if latin_name == "Xudayberdiev Otabek Talipovich":
                skipped += 1
                continue
            key = normalize_name(row.get("name_ru"))
            if key and key in seen_names:
                skipped += 1
                continue
            seen_names.add(key)
            role_ru = (row.get("role_ru") or "").lower()
            name_ru, name_latin = STAFF_NAME_FIXES.get(key, (row["name_ru"], ""))
            is_davronbek = latin_name == "Botirov Davronbek Baxtiyorovich"
            role_uz = "Bosh direktor oʻrinbosari" if is_davronbek else row["role_uz"]
            role_ru = "Заместитель Генерального директора" if is_davronbek else row["role_ru"]
            role_en = "Deputy General Director" if is_davronbek else row["role_en"]
            obj = TeamMember(
                full_name=name_latin or row["name_uz"] or STAFF_LATIN_NAMES.get(key) or row["name_ru"],
                full_name_ru=name_ru,
                role_uz=role_uz, role_ru=role_ru, role_en=role_en,
                certificates_uz=row.get("cert_uz", ""), certificates_ru=row.get("cert_ru", ""),
                certificates_en=row.get("cert_en", ""), dept=row["dept"],
                is_leadership=is_davronbek or any(word in role_ru.lower() for word in LEADERSHIP_WORDS),
                order=2 if is_davronbek else order,
            )
            if row.get("photo"):
                attach(obj.photo, row["photo"])
            obj.save()
        if skipped:
            # Konsol xabari ASCII: Windows konsoli kirill harflarini chiqara olmaydi
            self.stdout.write(f"Takror xodim otkazib yuborildi: {skipped}")

    def _certificates(self, staff: list[dict], certificates: list[dict]) -> None:
        """Sertifikat skanlari: xodimga asl (tuzatilmagan) name_ru boʻyicha, barcha ishonch darajalari."""
        members = {normalize_name(m.full_name_ru): m for m in TeamMember.objects.all()}
        for original, (fixed_ru, _latin) in STAFF_NAME_FIXES.items():
            if normalize_name(fixed_ru) in members:
                members[original] = members[normalize_name(fixed_ru)]
        orders: dict[int, int] = {}
        attached = skipped = 0
        for entry in certificates:
            member = members.get(normalize_name(entry.get("staff_name_ru")))
            if member is None:
                skipped += 1
                continue
            orders[member.pk] = orders.get(member.pk, -1) + 1
            obj = StaffCertificate(
                member=member, title=entry["title"][:255], issuer=(entry.get("issuer") or "")[:255],
                title_ru=(entry.get("title_ru") or "")[:255], title_en=(entry.get("title_en") or "")[:255],
                issuer_ru=(entry.get("issuer_ru") or "")[:255], issuer_en=(entry.get("issuer_en") or "")[:255],
                number=(entry.get("number") or "")[:80], issued_on=parse_date(entry.get("issued_on")),
                valid_until=parse_date(entry.get("valid_until")), order=orders[member.pk],
                scope_uz=entry.get("scope_uz") or "", scope_ru=entry.get("scope_ru") or "",
                scope_en=entry.get("scope_en") or "",
            )
            attach(obj.scan, entry.get("file"))
            obj.save()
            attached += 1
        # Konsol xabari ASCII
        self.stdout.write(f"Sertifikatlar: {attached} biriktirildi, {skipped} otkazib yuborildi")

    def _projects(self, projects: list[dict], directions: dict) -> None:
        rows = []
        for index, p in enumerate(projects, start=1):
            rows.append(Project(
                slug=f"{p['dept']}-{index:03d}", direction=directions[DEPT_TO_DIRECTION[p["dept"]]],
                order=index, year=p.get("year"), client=p.get("client", ""),
                title_uz=p["title_uz"][:200], title_ru=p["title_ru"][:200], title_en=p.get("title_en", "")[:200],
            ))
        Project.objects.bulk_create(rows)

    def _locations(self, entries: list[dict]) -> None:
        """Loyiha joylari `order` boʻyicha. `high` ochiq, `medium` yashirin, `none` saqlanmaydi.

        Xorijdagi ishlar (`abroad`) loyihada belgilanadi — reestrda koʻrinadi, xaritaga chiqmaydi.
        """
        projects = {p.order: p for p in Project.objects.all()}
        rows, abroad = [], []
        unknown_region = unknown_project = 0
        for entry in entries:
            project = projects.get(entry["order"])
            if project is None:
                unknown_project += 1
                continue
            if entry.get("abroad"):
                abroad.append(project.pk)
            confidence = entry.get("confidence")
            if confidence not in (ProjectLocation.CONFIDENCE_HIGH, ProjectLocation.CONFIDENCE_MEDIUM):
                continue
            for loc in entry.get("locations") or []:
                if loc.get("region") not in REGIONS:
                    unknown_region += 1
                    continue
                city_uz = loc.get("city_uz") or ""
                rows.append(ProjectLocation(
                    project=project, region=loc["region"], city_uz=city_uz, city_ru=loc.get("city_ru") or "",
                    city_en=CITY_EN.get(city_uz, city_uz), lat=loc.get("lat"), lon=loc.get("lon"),
                    confidence=confidence, evidence=loc.get("evidence") or "",
                    is_public=confidence == ProjectLocation.CONFIDENCE_HIGH,
                ))
        ProjectLocation.objects.bulk_create(rows)
        Project.objects.update(abroad=False)
        Project.objects.filter(pk__in=abroad).update(abroad=True)
        # Konsol xabari ASCII
        if unknown_region or unknown_project:
            self.stdout.write(f"Joylar: nomalum hudud {unknown_region}, nomalum loyiha {unknown_project} - otkazib yuborildi")

    def _clients(self, data: dict) -> None:
        valid = {key for key, _ in Client.SECTOR_CHOICES}
        unknown = {c["sector"] for c in data["clients"]} - valid
        if unknown:
            raise CommandError(f"clients.json da nomalum soha: {sorted(unknown)}")
        Client.objects.bulk_create([
            Client(name_uz=c["name_uz"], name_ru=c.get("name_ru", ""), name_en=c.get("name_en", ""),
                   sector=c["sector"], featured=c.get("featured", False), order=order)
            for order, c in enumerate(data["clients"])
        ])
