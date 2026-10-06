import re

from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from .models import (
    Branch, Client, Credential, Direction, Instrument, Lead, LegalAct, Post, Project,
    ProjectLocation, Service, SiteSettings, SiteText, Slide, StaffCertificate, Stat, TeamMember,
)
from .sitetext import LANGS, default_for

# Har qanday konversiya turi: forms.py da `%(mb)d` ham bor
PY_PLACEHOLDER = re.compile(r"%\((\w+)\)[sdifr]")
JS_PLACEHOLDER = re.compile(r"\{(\w+)\}")


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 0
    fields = ["order", "slug", "title_uz", "summary_uz"]


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Rekvizitlar", {"fields": [
            "brand_name", "brand_descriptor", "org_name_uz", "org_name_ru", "org_name_en",
            "tin", "founded_year", "phone", "phone_second", "phone_third", "email", "telegram",
            "address_uz", "address_ru", "address_en",
            "work_hours_uz", "work_hours_ru", "work_hours_en",
            "bank_details_uz", "bank_details_ru", "bank_details_en", "map_embed",
            "director_uz", "director_ru", "director_en",
            "map_lat", "map_lng", "experience_years", "staff_total", "staff_energy", "staff_supervision",
        ]}),
        ("Geroy bloki", {"fields": [
            "hero_kicker_uz", "hero_kicker_ru", "hero_kicker_en",
            "hero_title_uz", "hero_title_ru", "hero_title_en",
            "hero_accent_uz", "hero_accent_ru", "hero_accent_en",
            "seo_title_uz", "seo_title_ru", "seo_title_en",
            "hero_text_uz", "hero_text_ru", "hero_text_en",
            "hero_image", "report_turnaround_days",
        ]}),
        ("Brend rasmlari", {"fields": ["logo_mark", "logo_footer", "favicon", "og_image"]}),
        ("Kompaniya sahifasi", {"fields": [
            "about_uz", "about_ru", "about_en",
            "quality_policy_uz", "quality_policy_ru", "quality_policy_en",
        ]}),
    ]

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ["title_uz", "slug", "accent", "order"]
    list_editable = ["order"]
    prepopulated_fields = {"slug": ["title_uz"]}
    inlines = [ServiceInline]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["title_uz", "direction", "order"]
    list_filter = ["direction"]
    list_editable = ["order"]
    prepopulated_fields = {"slug": ["title_uz"]}


@admin.register(LegalAct)
class LegalActAdmin(admin.ModelAdmin):
    list_display = ["number", "title_uz", "verified_on", "effective_on", "order"]
    list_filter = ["verified_on"]
    list_editable = ["order"]
    filter_horizontal = ["directions"]


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["name_uz", "sector", "featured", "order"]
    list_filter = ["sector", "featured"]
    list_editable = ["featured", "order"]
    search_fields = ["name_uz", "name_ru"]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["city_uz", "head", "phone", "is_head_office", "order"]
    list_editable = ["order"]


class ProjectLocationInline(admin.TabularInline):
    model = ProjectLocation
    extra = 0
    fields = ["region", "city_uz", "city_ru", "city_en", "lat", "lon", "confidence", "is_public", "evidence"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["title_uz", "client", "direction", "year", "abroad", "order"]
    list_filter = ["direction", "year", "abroad"]
    list_editable = ["order"]
    search_fields = ["title_uz", "title_ru", "client"]
    prepopulated_fields = {"slug": ["title_uz"]}
    inlines = [ProjectLocationInline]


@admin.register(ProjectLocation)
class ProjectLocationAdmin(admin.ModelAdmin):
    """Taxminiy (medium) joylar yashirin: mijoz tasdiqlasa `is_public` belgilanadi."""
    list_display = ["project", "region", "city_uz", "confidence", "is_public", "evidence"]
    list_filter = ["region", "confidence", "is_public"]
    list_editable = ["is_public"]
    list_select_related = ["project"]
    search_fields = ["project__title_uz", "project__client", "city_uz", "evidence"]
    autocomplete_fields = ["project"]


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ["name_uz", "serial", "certificate_no", "verified_on", "valid_until", "order"]
    list_filter = ["direction"]
    list_editable = ["order"]


class StaffCertificateInline(admin.StackedInline):
    model = StaffCertificate
    extra = 0
    fields = [("title", "order"), ("title_ru", "title_en"), ("issuer", "number"), ("issuer_ru", "issuer_en"),
              ("issued_on", "valid_until"), "scan",
              "scope_uz", "scope_ru", "scope_en"]


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ["full_name", "role_uz", "dept", "is_leadership", "order"]
    list_filter = ["dept", "is_leadership"]
    list_editable = ["is_leadership", "order"]
    search_fields = ["full_name", "full_name_ru"]
    prepopulated_fields = {"slug": ["full_name"]}
    inlines = [StaffCertificateInline]


@admin.register(StaffCertificate)
class StaffCertificateAdmin(admin.ModelAdmin):
    list_display = ["title", "member", "issuer", "number", "issued_on", "valid_until"]
    list_filter = ["member__dept", "issuer", "valid_until"]
    search_fields = ["title", "number", "issuer", "member__full_name", "member__full_name_ru"]
    autocomplete_fields = ["member"]


@admin.register(Credential)
class CredentialAdmin(admin.ModelAdmin):
    list_display = ["kind", "number", "issuer_uz", "valid_until", "show_in_hero", "order"]
    list_filter = ["kind", "show_in_hero"]
    list_editable = ["show_in_hero", "order"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title_uz", "published_on", "legal_act", "is_published"]
    list_filter = ["is_published", "published_on"]
    prepopulated_fields = {"slug": ["title_uz"]}
    date_hierarchy = "published_on"


@admin.register(Stat)
class StatAdmin(admin.ModelAdmin):
    list_display = ["value", "label_uz", "highlight", "order"]
    list_editable = ["highlight", "order"]


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ["created_at", "name", "phone", "direction", "urgency", "status", "attachment_link"]
    list_filter = ["status", "urgency", "direction", "language"]
    search_fields = ["name", "phone", "email", "object_type", "note"]
    list_editable = ["status"]
    date_hierarchy = "created_at"
    readonly_fields = ["created_at", "source", "language", "attachment_link"]

    @admin.display(description="Faylni yuklab olish")
    def attachment_link(self, obj):
        """leads/ ommaga ochiq emas — fayl faqat xodim uchun view orqali beriladi."""
        if not obj.pk or not obj.attachment:
            return "—"
        return format_html('<a href="{}">{}</a>', reverse("lead_attachment", args=[obj.pk]), "Yuklab olish")


class SiteTextForm(forms.ModelForm):
    """Qayta yozuvda standart matndagi oʻrinbosarlar (%(n)s yoki {n}) aynan saqlanishi shart."""

    class Meta:
        model = SiteText
        fields = ["text_uz", "text_ru", "text_en"]
        widgets = {f"text_{lang}": forms.Textarea(attrs={"rows": 3, "cols": 90}) for lang in LANGS}

    def clean(self):
        cleaned = super().clean()
        pattern = JS_PLACEHOLDER if self.instance.kind == SiteText.KIND_WIDGET else PY_PLACEHOLDER
        expected = set(pattern.findall(self.instance.key if self.instance.kind == SiteText.KIND_UI
                                       else default_for(self.instance.kind, self.instance.key).get("uz", "")))
        for lang in LANGS:
            value = cleaned.get(f"text_{lang}") or ""
            if not value:
                continue
            found = set(pattern.findall(value))
            if found != expected:
                self.add_error(f"text_{lang}", "Oʻrinbosarlar standart matndagidek boʻlishi kerak: "
                               + (", ".join(sorted(expected)) or "oʻrinbosarsiz"))
            elif pattern is PY_PLACEHOLDER and "%" in PY_PLACEHOLDER.sub("", value).replace("%%", ""):
                self.add_error(f"text_{lang}", "Yakka «%» belgisini «%%» deb yozing.")
        return cleaned


@admin.register(SiteText)
class SiteTextAdmin(admin.ModelAdmin):
    """Saytdagi barcha interfeys matnlari. Boʻsh maydon — standart tarjima."""

    form = SiteTextForm
    list_display = ["short_key", "kind", "is_overridden", "updated_at"]
    list_filter = ["kind"]
    search_fields = ["key", "text_uz", "text_ru", "text_en"]
    readonly_fields = ["key", "kind", "defaults"]
    fieldsets = [
        (None, {"fields": ["kind", "key", "defaults"]}),
        ("Qayta yozuv (boʻsh qoldirilsa — standart matn)", {"fields": ["text_uz", "text_ru", "text_en"]}),
    ]

    def has_add_permission(self, request):
        # Roʻyxat `sync_site_content` buyrugʻi bilan shablonlardan toʻldiriladi
        return False

    @admin.display(description="Matn")
    def short_key(self, obj):
        return obj.key if len(obj.key) <= 90 else obj.key[:90] + "…"

    @admin.display(description="Oʻzgartirilgan", boolean=True)
    def is_overridden(self, obj):
        return any(obj.value(lang) for lang in LANGS)

    @admin.display(description="Standart matn")
    def defaults(self, obj):
        values = default_for(obj.kind, obj.key)
        return format_html_join("", "<p><b>{}:</b> {}</p>", ((lang, values.get(lang, "")) for lang in LANGS))


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ["thumb", "kicker_uz", "text_uz", "is_active", "order"]
    list_display_links = ["thumb", "kicker_uz"]
    list_editable = ["is_active", "order"]
    fields = ["image", "focus_y", ("kicker_uz", "kicker_ru", "kicker_en"), "text_uz", "text_ru", "text_en",
              "alt_uz", "alt_ru", "alt_en", ("is_active", "order")]

    @admin.display(description="Surat")
    def thumb(self, obj):
        if not obj.image:
            return "—"
        return format_html('<img src="{}" alt="" style="height:60px;border-radius:4px">', obj.image.url)
