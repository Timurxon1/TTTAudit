"""Sayt kontent modellari.

Tarjima: har bir matn maydoni `_uz / _ru / _en` ko'rinishida saqlanadi.
`tr("title")` joriy tilga mos qiymatni qaytaradi, bo'sh bo'lsa UZ ga qaytadi.
Shablonda: {{ obj|tr:"title" }}

Segment modeli yoʻq — «kimga kerak» boʻlimi saytda yoʻq.
"""
import re

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import get_language, gettext_lazy as _

from .geo.regions import REGION_CHOICES

MAX_IMAGE_UPLOAD_BYTES = 5 * 1024 * 1024  # admin yuklaydigan brend/slayd rasmlari


def validate_image_size(file) -> None:
    """Ommaga xizmat qilinadigan admin rasmlari uchun hajm chegarasi."""
    if file.size > MAX_IMAGE_UPLOAD_BYTES:
        raise ValidationError(_("Rasm hajmi %(mb)d MB dan oshmasligi kerak."),
                              params={"mb": MAX_IMAGE_UPLOAD_BYTES // (1024 * 1024)})


class TranslatableMixin:
    """`tr("field")` -> field_<til> yoki UZ fallback."""

    def tr(self, field: str) -> str:
        lang = (get_language() or "uz").split("-")[0]
        if lang not in {"uz", "ru", "en"}:
            lang = "uz"
        value = getattr(self, f"{field}_{lang}", "") or ""
        if not value:
            value = getattr(self, f"{field}_uz", "") or ""
        return value

    def tr_list(self, field: str) -> list:
        """JSON ro'yxat maydonlari uchun: [{"uz": "...", "ru": "..."}, ...]"""
        lang = (get_language() or "uz").split("-")[0]
        items = getattr(self, field, None) or []
        out = []
        for item in items:
            if isinstance(item, dict):
                out.append(item.get(lang) or item.get("uz") or "")
            else:
                out.append(str(item))
        return [i for i in out if i]


# ----------------------------------------------------------------- sozlamalar
class SiteSettings(TranslatableMixin, models.Model):
    org_name_uz = models.CharField(
        _("Tashkilot (rasmiy nomi)"), max_length=120, default="«TTTaudit» MChJ",
    )
    org_name_ru = models.CharField(max_length=120, blank=True)
    org_name_en = models.CharField(max_length=120, blank=True)
    brand_name = models.CharField(
        _("Logotip belgisi"), max_length=60, default="TTT AUDIT",
        help_text=_("Logotipdagi yirik qism. Qisqa boʻlgani maʼqul."),
    )
    brand_descriptor = models.CharField(
        _("Logotip ostidagi qator"), max_length=80, default="Energoaudit · nazorat oʻlchovi",
        blank=True,
        help_text=_("Belgining ostida mayda harflarda beriladi."),
    )
    phone = models.CharField(_("Telefon"), max_length=40, default="+998 00 000 00 00")
    phone_second = models.CharField(_("Qoʻshimcha telefon"), max_length=40, blank=True)
    phone_third = models.CharField(_("Uchinchi telefon"), max_length=40, blank=True)
    email = models.EmailField(_("E-pochta"), default="info@example.uz")
    telegram = models.CharField(max_length=80, blank=True)
    address_uz = models.CharField(max_length=200, default="Toshkent sh.")
    address_ru = models.CharField(max_length=200, blank=True)
    address_en = models.CharField(max_length=200, blank=True)
    map_embed = models.TextField(_("Xarita iframe kodi"), blank=True)
    work_hours_uz = models.CharField(max_length=120, default="")
    work_hours_ru = models.CharField(max_length=120, blank=True)
    work_hours_en = models.CharField(max_length=120, blank=True)
    tin = models.CharField(_("STIR"), max_length=20, default="000 000 000")
    bank_details_uz = models.TextField(blank=True)
    bank_details_ru = models.TextField(blank=True)
    bank_details_en = models.TextField(blank=True)
    founded_year = models.PositiveIntegerField(_("Tashkil topgan yil"), default=1997)

    director_uz = models.CharField(_("Rahbar"), max_length=120, blank=True)
    director_ru = models.CharField(max_length=120, blank=True)
    director_en = models.CharField(max_length=120, blank=True)
    office_tashkent_uz = models.CharField(_("Toshkent ofisi"), max_length=200, blank=True)
    office_tashkent_ru = models.CharField(max_length=200, blank=True)
    office_tashkent_en = models.CharField(max_length=200, blank=True)
    map_lat = models.FloatField(null=True, blank=True)
    map_lng = models.FloatField(null=True, blank=True)
    experience_years = models.PositiveSmallIntegerField(default=29)
    staff_total = models.PositiveSmallIntegerField(default=50)
    staff_energy = models.PositiveSmallIntegerField(default=24)
    staff_supervision = models.PositiveSmallIntegerField(default=16)

    hero_kicker_uz = models.CharField(max_length=160, default="Ekspert tashkiloti · Fargʻona · 1997-yildan")
    hero_kicker_ru = models.CharField(max_length=160, blank=True)
    hero_kicker_en = models.CharField(max_length=160, blank=True)
    hero_title_uz = models.CharField(
        max_length=200,
        default="Energoaudit va qurilishda nazorat oʻlchovi",
    )
    hero_title_ru = models.CharField(max_length=200, blank=True)
    hero_title_en = models.CharField(max_length=200, blank=True)
    hero_accent_uz = models.CharField(
        _("Sarlavhaning urgʻuli qatori"), max_length=200, blank=True,
        default="",
        help_text=_("Sarlavhaning ikkinchi qatori — urgʻu rangida beriladi."),
    )
    hero_accent_ru = models.CharField(max_length=200, blank=True)
    hero_accent_en = models.CharField(max_length=200, blank=True)
    seo_title_uz = models.CharField(
        _("Qidiruv sarlavhasi"), max_length=200, blank=True,
        default="Energoaudit va qurilishda nazorat oʻlchovi — TTT Audit, Fargʻona",
        help_text=_(
            "Brauzer yorligʻi va qidiruv natijasi uchun. Geroy gapidan farq "
            "qiladi: bu yerda kalit soʻzlar boʻlishi kerak."
        ),
    )
    seo_title_ru = models.CharField(max_length=200, blank=True)
    seo_title_en = models.CharField(max_length=200, blank=True)
    hero_text_uz = models.TextField(
        default=(
            "Majburiy energoaudit va bino energopasporti, bajarilgan ish "
            "hajmlarining nazorat oʻlchovi, loyiha-smeta hujjatlari "
            "ekspertizasi va texnik nazorat. Xulosa davlat organi, bank va "
            "sud uchun dalil boʻladi."
        )
    )
    hero_text_ru = models.TextField(blank=True)
    hero_text_en = models.TextField(blank=True)
    hero_image = models.ImageField(
        _("Geroy kadri"), upload_to="hero/", blank=True, null=True,
        help_text=_("Boʻsh boʻlsa blok suratsiz chiqadi. Stok foto ishlatilmaydi."),
    )
    # Brend rasmlari: boʻsh boʻlsa static/core/img/ dagi standart fayl ishlatiladi
    logo_mark = models.ImageField(
        _("Logotip (sarlavha)"), upload_to="branding/", blank=True, null=True, validators=[validate_image_size],
        help_text=_("Kvadrat PNG, kamida 88×88 px. Boʻsh boʻlsa standart logotip."),
    )
    logo_footer = models.ImageField(
        _("Logotip (pastki qism, oq)"), upload_to="branding/", blank=True, null=True, validators=[validate_image_size],
        help_text=_("Toʻq fonda koʻrinadigan oq variant, kamida 144×144 px."),
    )
    favicon = models.ImageField(
        _("Brauzer belgisi (favicon)"), upload_to="branding/", blank=True, null=True, validators=[validate_image_size],
        help_text=_("Kvadrat PNG, 180×180 px."),
    )
    og_image = models.ImageField(
        _("Ijtimoiy tarmoq surati (OG)"), upload_to="branding/", blank=True, null=True, validators=[validate_image_size],
        help_text=_("Havola ulashilganda chiqadi, 1200×630 px."),
    )
    report_turnaround_days = models.PositiveIntegerField(
        _("Xulosa muddati, ish kuni"), null=True, blank=True,
        help_text=_("Boʻsh boʻlsa saytda koʻrsatilmaydi. Faqat mijoz tasdiqlagan raqam."),
    )

    about_uz = models.TextField(blank=True)
    about_ru = models.TextField(blank=True)
    about_en = models.TextField(blank=True)
    quality_policy_uz = models.TextField(blank=True)
    quality_policy_ru = models.TextField(blank=True)
    quality_policy_en = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Sayt sozlamalari")
        verbose_name_plural = _("Sayt sozlamalari")

    def __str__(self):
        return self.org_name_uz

    @classmethod
    def load(cls):
        return cls.objects.first() or cls.objects.create()


# ----------------------------------------------------------------- yo'nalish
class Direction(TranslatableMixin, models.Model):
    ACCENT_STEEL = "steel"
    ACCENT_AMBER = "amber"
    ACCENT_CHOICES = [
        (ACCENT_STEEL, _("Sovuq — oʻlchov auditi")),
        (ACCENT_AMBER, _("Issiq — energoaudit")),
    ]

    slug = models.SlugField(unique=True)
    order = models.PositiveSmallIntegerField(default=0)
    accent = models.CharField(max_length=8, choices=ACCENT_CHOICES, default=ACCENT_STEEL)

    kicker_uz = models.CharField(max_length=80, default="Yoʻnalish")
    kicker_ru = models.CharField(max_length=80, blank=True)
    kicker_en = models.CharField(max_length=80, blank=True)
    title_uz = models.CharField(max_length=140)
    title_ru = models.CharField(max_length=140, blank=True)
    title_en = models.CharField(max_length=140, blank=True)
    summary_uz = models.TextField()
    summary_ru = models.TextField(blank=True)
    summary_en = models.TextField(blank=True)

    # Sahifa ichi
    problem_title_uz = models.CharField(max_length=200, blank=True)
    problem_title_ru = models.CharField(max_length=200, blank=True)
    problem_title_en = models.CharField(max_length=200, blank=True)
    problem_body_uz = models.TextField(blank=True)
    problem_body_ru = models.TextField(blank=True)
    problem_body_en = models.TextField(blank=True)
    legal_note_uz = models.TextField(blank=True)
    legal_note_ru = models.TextField(blank=True)
    legal_note_en = models.TextField(blank=True)

    process = models.JSONField(
        default=list, blank=True,
        help_text=_('[{"uz": "Qadam", "ru": "...", "en": "..."}] koʻrinishida'),
    )
    deliverables = models.JSONField(default=list, blank=True)

    image = models.ImageField(upload_to="directions/", blank=True, null=True)

    class Meta:
        ordering = ["order"]
        verbose_name = _("Yoʻnalish")
        verbose_name_plural = _("Yoʻnalishlar")

    def __str__(self):
        return self.title_uz

    def get_absolute_url(self):
        return reverse("core:direction", args=[self.slug])

    @property
    def hero_kind(self):
        """Generativ tasvir turi: issiq yo'nalish -> termogramma."""
        return "facade" if self.accent == self.ACCENT_AMBER else "measured"


class Service(TranslatableMixin, models.Model):
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE, related_name="services")
    slug = models.SlugField()
    order = models.PositiveSmallIntegerField(default=0)

    title_uz = models.CharField(max_length=140)
    title_ru = models.CharField(max_length=140, blank=True)
    title_en = models.CharField(max_length=140, blank=True)
    summary_uz = models.CharField(max_length=220)
    summary_ru = models.CharField(max_length=220, blank=True)
    summary_en = models.CharField(max_length=220, blank=True)
    body_uz = models.TextField(blank=True)
    body_ru = models.TextField(blank=True)
    body_en = models.TextField(blank=True)

    process = models.JSONField(default=list, blank=True)
    deliverables = models.JSONField(default=list, blank=True)
    faq = models.JSONField(
        default=list, blank=True,
        help_text=_('[{"q": {"uz": "..."}, "a": {"uz": "..."}}]'),
    )
    duration_uz = models.CharField(max_length=80, blank=True)
    duration_ru = models.CharField(max_length=80, blank=True)
    duration_en = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["direction__order", "order"]
        unique_together = [("direction", "slug")]
        verbose_name = _("Xizmat")
        verbose_name_plural = _("Xizmatlar")

    def __str__(self):
        return self.title_uz

    def get_absolute_url(self):
        return reverse("core:service", args=[self.direction.slug, self.slug])

    def faq_pairs(self):
        lang = (get_language() or "uz").split("-")[0]
        pairs = []
        for item in self.faq or []:
            q = (item.get("q") or {})
            a = (item.get("a") or {})
            pairs.append({
                "q": q.get(lang) or q.get("uz") or "",
                "a": a.get(lang) or a.get("uz") or "",
            })
        return [p for p in pairs if p["q"]]


# ----------------------------------------------------------------- qonunchilik
class LegalAct(TranslatableMixin, models.Model):
    number = models.CharField(_("Raqami"), max_length=60)
    order = models.PositiveSmallIntegerField(default=0)
    directions = models.ManyToManyField(Direction, blank=True, related_name="legal_acts")

    title_uz = models.CharField(max_length=250)
    title_ru = models.CharField(max_length=250, blank=True)
    title_en = models.CharField(max_length=250, blank=True)
    adopted_on = models.DateField(null=True, blank=True)
    effective_on = models.DateField(null=True, blank=True)
    applies_to_uz = models.CharField(max_length=250, blank=True)
    applies_to_ru = models.CharField(max_length=250, blank=True)
    applies_to_en = models.CharField(max_length=250, blank=True)
    requirement_uz = models.TextField(blank=True)
    requirement_ru = models.TextField(blank=True)
    requirement_en = models.TextField(blank=True)
    deadline_uz = models.CharField(max_length=160, blank=True)
    deadline_ru = models.CharField(max_length=160, blank=True)
    deadline_en = models.CharField(max_length=160, blank=True)
    lex_url = models.URLField(blank=True)
    verified_on = models.DateField(
        _("lex.uz bilan tekshirilgan sana"), null=True, blank=True,
        help_text=_(
            "Boʻsh boʻlsa hujjat saytda koʻrsatilmaydi. Raqam, nom va talabni "
            "amaldagi tahrir bilan solishtirgandan keyingina toʻldiring."
        ),
    )

    class Meta:
        ordering = ["order"]
        verbose_name = _("Meʼyoriy hujjat")
        verbose_name_plural = _("Qonunchilik")

    def __str__(self):
        return f"{self.number} — {self.title_uz[:50]}"


# ----------------------------------------------------------------- loyihalar
class Project(TranslatableMixin, models.Model):
    slug = models.SlugField(unique=True)
    direction = models.ForeignKey(Direction, on_delete=models.SET_NULL, null=True, related_name="projects")
    order = models.PositiveSmallIntegerField(default=0)
    year = models.PositiveIntegerField(null=True, blank=True)
    client = models.CharField(_("Buyurtmachi"), max_length=250, blank=True)
    region_uz = models.CharField(max_length=80, blank=True)
    region_ru = models.CharField(max_length=80, blank=True)
    region_en = models.CharField(max_length=80, blank=True)

    title_uz = models.CharField(max_length=200, help_text=_("Anonim: «4 qavatli maʼmuriy bino»"))
    title_ru = models.CharField(max_length=200, blank=True)
    title_en = models.CharField(max_length=200, blank=True)
    object_type_uz = models.CharField(max_length=120, blank=True)
    object_type_ru = models.CharField(max_length=120, blank=True)
    object_type_en = models.CharField(max_length=120, blank=True)

    task_uz = models.TextField(blank=True)
    task_ru = models.TextField(blank=True)
    task_en = models.TextField(blank=True)
    result_uz = models.TextField(blank=True)
    result_ru = models.TextField(blank=True)
    result_en = models.TextField(blank=True)

    estimate_value = models.CharField(_("Smeta qiymati"), max_length=60, blank=True)
    difference_found = models.CharField(_("Aniqlangan farq"), max_length=60, blank=True)
    energy_category = models.CharField(_("Energiya toifasi"), max_length=2, blank=True)

    hero_image = models.ImageField(upload_to="projects/", blank=True, null=True)
    abroad = models.BooleanField(_("Xorijda"), default=False, help_text=_("Reestrda koʻrsatiladi, xaritada emas."))

    class Meta:
        ordering = ["-year", "order", "pk"]
        verbose_name = _("Loyiha")
        verbose_name_plural = _("Loyihalar")

    def __str__(self):
        return self.title_uz


class ProjectLocation(TranslatableMixin, models.Model):
    """Loyiha joyi: ish nomi yoki buyurtmachisida koʻrsatilgan hudud (va shahar, boʻlsa).

    `high` — joy matnda aniq yozilgan, xaritada darhol chiqadi; `medium` — taxmin, admin tasdiqlaguncha
    (`is_public`) yashirin. Koordinatasiz joy faqat hudud boʻyoqida hisoblanadi, belgi qoʻyilmaydi.
    """
    CONFIDENCE_HIGH = "high"
    CONFIDENCE_MEDIUM = "medium"
    CONFIDENCE_CHOICES = [(CONFIDENCE_HIGH, _("Aniq")), (CONFIDENCE_MEDIUM, _("Taxminiy"))]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="locations")
    region = models.CharField(_("Hudud"), max_length=20, choices=REGION_CHOICES)
    city_uz = models.CharField(_("Shahar"), max_length=80, blank=True)
    city_ru = models.CharField(max_length=80, blank=True)
    city_en = models.CharField(max_length=80, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    confidence = models.CharField(_("Ishonch"), max_length=8, choices=CONFIDENCE_CHOICES, default=CONFIDENCE_HIGH)
    evidence = models.TextField(_("Asos (matndan)"), blank=True)
    is_public = models.BooleanField(_("Xaritada koʻrsatish"), default=True)

    class Meta:
        ordering = ["project__order", "pk"]
        verbose_name = _("Loyiha joyi")
        verbose_name_plural = _("Loyihalar joyi")

    def __str__(self):
        return f"{self.project_id}: {self.region} {self.city_uz}".strip()


# ----------------------------------------------------------------- asboblar
class Instrument(TranslatableMixin, models.Model):
    name_uz = models.CharField(max_length=140)
    name_ru = models.CharField(max_length=140, blank=True)
    name_en = models.CharField(max_length=140, blank=True)
    model_name = models.CharField(_("Model"), max_length=120, blank=True)
    serial = models.CharField(_("Zavod raqami"), max_length=60, blank=True)
    valid_until = models.DateField(_("Qiyoslash amal qiladi"), null=True, blank=True)
    range_uz = models.CharField(_("Oʻlchov chegarasi"), max_length=160, blank=True)
    range_ru = models.CharField(max_length=160, blank=True)
    range_en = models.CharField(max_length=160, blank=True)
    purpose_uz = models.CharField(max_length=220, blank=True)
    purpose_ru = models.CharField(max_length=220, blank=True)
    purpose_en = models.CharField(max_length=220, blank=True)
    direction = models.ForeignKey(Direction, on_delete=models.SET_NULL, null=True, blank=True, related_name="instruments")
    verified_on = models.DateField(_("Metrologik tekshiruv"), null=True, blank=True)
    certificate_no = models.CharField(_("Sertifikat raqami"), max_length=60, blank=True)
    photo = models.ImageField(upload_to="instruments/", blank=True, null=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = _("Asbob")
        verbose_name_plural = _("Asboblar")

    def __str__(self):
        return self.name_uz


# ----------------------------------------------------------------- jamoa
class TeamMember(TranslatableMixin, models.Model):
    full_name = models.CharField(
        _("Ism familiya"), max_length=120, help_text=_("Lotin yozuvida — uz va en sahifalar uchun")
    )
    full_name_ru = models.CharField(
        _("Ism familiya (kirill)"), max_length=120, blank=True,
        help_text=_("Rus sahifasi uchun. Boʻsh boʻlsa lotin yozuvi ishlatiladi."),
    )
    slug = models.SlugField(
        max_length=140, unique=True, help_text=_("Profil manzili: /jamoa/<slug>/ (lotin ismidan)"),
    )
    email = models.EmailField(blank=True)
    DEPT_MANAGEMENT = "management"
    DEPT_ENERGY = "energy"
    DEPT_CONSTRUCTION = "construction"
    DEPT_CHOICES = [
        (DEPT_MANAGEMENT, _("Rahbariyat")),
        (DEPT_ENERGY, _("Energoaudit")),
        (DEPT_CONSTRUCTION, _("Qurilishda nazorat oʻlchovi")),
    ]
    dept = models.CharField(_("Boʻlim"), max_length=16, choices=DEPT_CHOICES, default=DEPT_ENERGY)
    is_leadership = models.BooleanField(_("Rahbariyat"), default=False)
    cv = models.JSONField(
        _("Maʼlumoti va malakasi"), default=dict, blank=True,
        help_text=_('{"ru": [{"title": "Образование", "lines": ["..."]}], "uz": [...], "en": [...]}'),
    )
    role_uz = models.CharField(max_length=120)
    role_ru = models.CharField(max_length=120, blank=True)
    role_en = models.CharField(max_length=120, blank=True)
    speciality_uz = models.CharField(max_length=200, blank=True)
    speciality_ru = models.CharField(max_length=200, blank=True)
    speciality_en = models.CharField(max_length=200, blank=True)
    experience_years = models.PositiveSmallIntegerField(null=True, blank=True)
    certificates_uz = models.TextField(blank=True, help_text=_("Har qatorda bitta"))
    certificates_ru = models.TextField(blank=True)
    certificates_en = models.TextField(blank=True)
    education = models.JSONField(
        _("Maʼlumoti"), default=list, blank=True,
        help_text='[{"years": "2004", "uz": "...", "ru": "...", "en": "..."}]',
    )
    experience = models.JSONField(
        _("Ish tajribasi"), default=list, blank=True,
        help_text='[{"years": "1979–1989", "uz": "...", "ru": "...", "en": "..."}]',
    )
    photo = models.ImageField(upload_to="team/", blank=True, null=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-is_leadership", "order"]
        verbose_name = _("Mutaxassis")
        verbose_name_plural = _("Rahbariyat va mutaxassislar")

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_member_slug(self.full_name, exclude_pk=self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:team_member", args=[self.slug])

    @property
    def photo_has_band(self) -> bool:
        """Eski byulleten suratidagi rangli chiziqni kesamiz; yangi portretlarni kattalashtirmaymiz."""
        if self.dept == self.DEPT_MANAGEMENT or not self.photo:
            return False
        filename = self.photo.name.rsplit("/", 1)[-1].lower()
        is_new_portrait = filename.startswith("photo_2026-09-30_") or filename in {
            "botirov_davronbek_baxtiyorovich.jpg",
            "jasur_jorayev.jpg",
            "nuraliyev_shukurullo.jpg",
            "nuraliyev_shukrullo_rustamjon_ogli.jpg",
        }
        return not is_new_portrait

    def timeline(self, field: str) -> list[dict]:
        """`education` / `experience`: [{"years": ..., "text": ...}] joriy tilda (UZ ga qaytadi)."""
        lang = current_lang()
        rows = []
        for item in getattr(self, field, None) or []:
            if not isinstance(item, dict):
                continue
            years = item.get("years") or ""
            if isinstance(years, dict):
                years = years.get(lang) or years.get("uz") or ""
            text = item.get(lang) or item.get("uz") or ""
            if text:
                rows.append({"years": years, "text": text})
        return rows

    def education_rows(self):
        return self.timeline("education")

    def experience_rows(self):
        return self.timeline("experience")

    def certificate_lines(self):
        return [line.strip() for line in self.tr("certificates").splitlines() if line.strip()]

    def display_name(self) -> str:
        lang = (get_language() or "uz").split("-")[0]
        if lang == "ru" and self.full_name_ru:
            # Byulletendagi kirill ismlar KATTA harfda — sahifada «Султонов Рўзиматжон» koʻrinishida
            return self.full_name_ru.title() if self.full_name_ru.isupper() else self.full_name_ru
        return self.full_name

    def cv_sections(self) -> list:
        """Joriy tildagi boʻlimlar; yoʻq boʻlsa rus tilidagisi (eski saytda eng toʻliq)."""
        lang = (get_language() or "uz").split("-")[0]
        data = self.cv or {}
        return data.get(lang) or data.get("ru") or []


def current_lang() -> str:
    lang = (get_language() or "uz").split("-")[0]
    return lang if lang in {"uz", "ru", "en"} else "uz"


def member_slug(name: str) -> str:
    """«Joʻraev Jasur Alisher Oʻgʻli» -> "joraev-jasur-alisher-ogli" (ʻ ʼ ' olib tashlanadi)."""
    return slugify(re.sub(r"[ʻʼ'‘’`]", "", name or "")) or "xodim"


def unique_member_slug(name: str, exclude_pk=None) -> str:
    base = member_slug(name)[:130]
    slug, n = base, 2
    while TeamMember.objects.filter(slug=slug).exclude(pk=exclude_pk).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


class StaffCertificate(TranslatableMixin, models.Model):
    """Xodimning shaxsiy sertifikati (byulletendagi skan)."""

    member = models.ForeignKey(
        TeamMember, on_delete=models.CASCADE, related_name="certificates", verbose_name=_("Mutaxassis"),
    )
    scan = models.ImageField(_("Skan"), upload_to="team/certificates/", blank=True, null=True)
    # `title`/`issuer` — hujjatdagi asl yozuv (UZ fallback); `_ru/_en` — tarjimasi
    title = models.CharField(_("Nomi"), max_length=255)
    title_ru = models.CharField(max_length=255, blank=True)
    title_en = models.CharField(max_length=255, blank=True)
    issuer = models.CharField(_("Bergan tashkilot"), max_length=255, blank=True)
    issuer_ru = models.CharField(max_length=255, blank=True)
    issuer_en = models.CharField(max_length=255, blank=True)
    number = models.CharField(_("Raqam"), max_length=80, blank=True)
    issued_on = models.DateField(_("Berilgan sana"), null=True, blank=True)
    valid_until = models.DateField(_("Amal qilish muddati"), null=True, blank=True)
    scope_uz = models.TextField(blank=True)
    scope_ru = models.TextField(blank=True)
    scope_en = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["member", "order", "pk"]
        verbose_name = _("Xodim sertifikati")
        verbose_name_plural = _("Xodim sertifikatlari")

    def __str__(self):
        return f"{self.member} — {self.title}"

    def tr(self, field: str) -> str:
        """`title`/`issuer` asosiy maydoni `_uz` qoʻshimchasiz — fallback shu maydonning oʻzi."""
        if field in ("title", "issuer"):
            lang = (get_language() or "uz").split("-")[0]
            return getattr(self, f"{field}_{lang}", "") or getattr(self, field)
        return super().tr(field)


# ----------------------------------------------------------------- hujjatlar
class Credential(TranslatableMixin, models.Model):
    KIND_LICENSE = "license"
    KIND_ACCREDITATION = "accreditation"
    KIND_CERTIFICATE = "certificate"
    KIND_RATING = "rating"
    KIND_MEMBERSHIP = "membership"
    KIND_REGISTRY = "registry"
    KIND_INSURANCE = "insurance"
    KIND_CHOICES = [
        (KIND_LICENSE, _("Litsenziya")),
        (KIND_ACCREDITATION, _("Akkreditatsiya")),
        (KIND_CERTIFICATE, _("Sertifikat")),
        (KIND_RATING, _("Reyting")),
        (KIND_MEMBERSHIP, _("Aʼzolik")),
        (KIND_REGISTRY, _("Reestr")),
        (KIND_INSURANCE, _("Sugʻurta")),
    ]

    kind = models.CharField(max_length=16, choices=KIND_CHOICES, default=KIND_LICENSE)
    number = models.CharField(_("Raqam"), max_length=60)
    issuer_uz = models.CharField(max_length=160, blank=True)
    issuer_ru = models.CharField(max_length=160, blank=True)
    issuer_en = models.CharField(max_length=160, blank=True)
    scope_uz = models.CharField(max_length=250, blank=True)
    scope_ru = models.CharField(max_length=250, blank=True)
    scope_en = models.CharField(max_length=250, blank=True)
    issued_on = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    scan = models.FileField(upload_to="credentials/", blank=True, null=True)
    show_in_hero = models.BooleanField(_("Geroy ostida"), default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = _("Hujjat")
        verbose_name_plural = _("Litsenziya va akkreditatsiya")

    def __str__(self):
        return f"{self.get_kind_display()} {self.number}"


# ----------------------------------------------------------------- blog
class Post(TranslatableMixin, models.Model):
    slug = models.SlugField(unique=True)
    published_on = models.DateField()
    is_published = models.BooleanField(
        _("Saytda"), default=True,
        help_text=_("Qonunga tayangan maqola manba tekshirilmaguncha oʻchiq turadi."),
    )
    legal_act = models.ForeignKey(LegalAct, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")

    title_uz = models.CharField(max_length=220)
    title_ru = models.CharField(max_length=220, blank=True)
    title_en = models.CharField(max_length=220, blank=True)
    excerpt_uz = models.CharField(max_length=300)
    excerpt_ru = models.CharField(max_length=300, blank=True)
    excerpt_en = models.CharField(max_length=300, blank=True)
    body_uz = models.TextField()
    body_ru = models.TextField(blank=True)
    body_en = models.TextField(blank=True)

    class Meta:
        ordering = ["-published_on"]
        verbose_name = _("Maqola")
        verbose_name_plural = _("Yangiliklar")

    def __str__(self):
        return self.title_uz

    def get_absolute_url(self):
        return reverse("core:post", args=[self.slug])


# ----------------------------------------------------------------- raqamlar
class Stat(TranslatableMixin, models.Model):
    value = models.CharField(_("Qiymat"), max_length=32)
    label_uz = models.CharField(max_length=80)
    label_ru = models.CharField(max_length=80, blank=True)
    label_en = models.CharField(max_length=80, blank=True)
    highlight = models.BooleanField(
        _("Urgʻu bilan"), default=False,
        help_text=_("Bir vaqtda faqat bitta raqam — issiq nuqta qoidasi."),
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = _("Raqam")
        verbose_name_plural = _("Raqamlar chizigʻi")

    def __str__(self):
        return f"{self.value} — {self.label_uz}"


# ----------------------------------------------------------------- mijozlar
class Client(TranslatableMixin, models.Model):
    """Xizmat koʻrsatilgan tashkilot. Manba: data/tttaudit/clients.json."""

    SECTOR_ENERGY = "energy"
    SECTOR_CONSTRUCTION = "construction"
    SECTOR_CHOICES = [
        (SECTOR_ENERGY, _("Energetika va neft-gaz")),
        (SECTOR_CONSTRUCTION, _("Qurilish va suv xoʻjaligi")),
        ("industry", _("Sanoat")),
        ("agro", _("Agrosanoat va oziq-ovqat")),
        ("services", _("Savdo, transport va xizmatlar")),
        ("public", _("Xalqaro loyihalar va jamoat tashkilotlari")),
    ]

    name_uz = models.CharField(max_length=200)
    name_ru = models.CharField(max_length=200, blank=True)
    name_en = models.CharField(max_length=200, blank=True)
    sector = models.CharField(max_length=16, choices=SECTOR_CHOICES)
    featured = models.BooleanField(
        _("Bosh sahifada"), default=False,
        help_text=_("Energetika va qurilish yoʻnalishiga yaqin, taniqli tashkilotlar."),
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = _("Mijoz")
        verbose_name_plural = _("Mijozlar")

    def __str__(self):
        return self.name_uz


class Branch(TranslatableMixin, models.Model):
    city_uz = models.CharField(max_length=80)
    city_ru = models.CharField(max_length=80, blank=True)
    city_en = models.CharField(max_length=80, blank=True)
    address_uz = models.CharField(max_length=200, blank=True)
    address_ru = models.CharField(max_length=200, blank=True)
    address_en = models.CharField(max_length=200, blank=True)
    head = models.CharField(_("Masʼul"), max_length=120, blank=True)
    phone = models.CharField(_("Telefon"), max_length=40, blank=True)
    is_head_office = models.BooleanField(_("Bosh ofis"), default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = _("Ofis")
        verbose_name_plural = _("Ofislar")

    def __str__(self):
        return self.city_uz


# ----------------------------------------------------------------- so'rov
class Lead(models.Model):
    URGENCY_PLANNED = "planned"
    URGENCY_URGENT = "urgent"
    URGENCY_CHOICES = [
        (URGENCY_PLANNED, _("Rejali")),
        (URGENCY_URGENT, _("Shoshilinch")),
    ]
    STATUS_NEW = "new"
    STATUS_CHOICES = [
        (STATUS_NEW, _("Yangi")),
        ("contacted", _("Bogʻlanildi")),
        ("quoted", _("Taklif yuborildi")),
        ("won", _("Shartnoma")),
        ("lost", _("Yopildi")),
    ]

    direction = models.ForeignKey(Direction, on_delete=models.SET_NULL, null=True, blank=True)
    object_type = models.CharField(_("Obyekt turi"), max_length=120, blank=True)
    region = models.CharField(_("Viloyat"), max_length=80, blank=True)
    area_m2 = models.PositiveIntegerField(_("Maydon, m2"), null=True, blank=True)
    annual_kwh = models.PositiveIntegerField(_("Yillik isteʼmol"), null=True, blank=True)
    estimate_value = models.CharField(_("Smeta qiymati"), max_length=60, blank=True)
    urgency = models.CharField(max_length=16, choices=URGENCY_CHOICES, default=URGENCY_PLANNED)

    name = models.CharField(_("Ism"), max_length=120)
    phone = models.CharField(_("Telefon"), max_length=40)
    email = models.EmailField(blank=True)
    note = models.TextField(_("Izoh"), blank=True)
    attachment = models.FileField(_("Fayl"), upload_to="leads/%Y/%m/", blank=True, null=True)

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_NEW)
    source = models.CharField(max_length=200, blank=True)
    language = models.CharField(max_length=8, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Soʻrov")
        verbose_name_plural = _("Soʻrovlar")

    def __str__(self):
        return f"{self.name} · {self.phone} · {self.created_at:%Y-%m-%d}"


# Admin paneldan tahrirlanadigan sayt matnlari va slaydlar (alohida modul — fayl hajmi)
from .site_models import SiteText, Slide  # noqa: E402,F401
