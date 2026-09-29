"""Barcha sahifalar serverda render qilinadi. React faqat [data-react] orollari uchun."""
import json
import math

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from . import compliance, energy, home as home_data, maps, throttle
from .forms import LeadForm
from .models import (
    Credential,
    Direction,
    Instrument,
    LegalAct,
    Post,
    Project,
    Service,
    SiteSettings,
    Slide,
    Stat,
    TeamMember,
)
from .notify import notify_telegram


def page(request, template, nav="", crumbs=(), **context):
    """Umumiy render: `nav` — faol menyu kaliti, `crumbs` — [(sarlavha, url|None), ...]."""
    context.update({"nav": nav, "crumbs": list(crumbs)})
    return render(request, template, context)


def form_context():
    """Murojaat formasi vidjeti uchun umumiy kontekst."""
    directions = list(Direction.objects.all())
    return {
        "form_directions": directions,
        "form_directions_json": json.dumps(
            [{"id": d.pk, "title": d.tr("title"), "accent": d.accent, "slug": d.slug} for d in directions],
            ensure_ascii=False,
        ),
        "max_upload_mb": settings.LEAD_MAX_UPLOAD_BYTES // (1024 * 1024),
    }


def compliance_context():
    return {"compliance": {
        "passport_area": compliance.PASSPORT_AREA_M2,
        "registry_kwh": compliance.REGISTRY_KWH,
        "registry_gas": compliance.REGISTRY_GAS_M3,
        "periodic_years": compliance.PERIODIC_YEARS,
    }}


def energy_context():
    # Toifa chegaralari tasdiqlanmaguncha shkala sahifaga ham, vidjetga ham berilmaydi
    ladder = energy.ladder() if energy.BANDS_VERIFIED else []
    return {
        "energy_ladder": ladder,
        "energy_ladder_json": json.dumps(ladder, ensure_ascii=False),
        "passport_threshold": energy.PASSPORT_AREA_THRESHOLD_M2,
    }


HOME_FAQ = [
    (_("Energoaudit kimga majburiy?"),
     _("ЗРУ-940 ga koʻra davriy energoaudit majburiy tartibda besh yilda kamida bir marta oʻtkaziladi. "
       "Davlat energetika reestriga kiritilgan korxonalar va davlat ishtirokidagi tashkilotlar uchun "
       "audit majburiy; boshqalar uchun ixtiyoriy.")),
    (_("Qaysi binolarga energosamaradorlik toifasi belgilanadi?"),
     _("Foydalaniladigan maydoni 200 m² dan katta bino va inshootlarga. Energopasport yangi, mavjud, "
       "rekonstruksiya va modernizatsiya qilinayotgan obyektlar uchun rasmiylashtiriladi.")),
    (_("Nazorat oʻlchovi uchun qurilishni toʻxtatish kerakmi?"),
     _("Yoʻq. Oʻlchov ish jarayoniga xalaqit bermaydi; yashirin ishlar yopilishidan oldin qayd etiladi.")),
    (_("Ishlab chiqarishni toʻxtatmasdan energoaudit qilsa boʻladimi?"),
     _("Ha — aksincha, oʻlchovlar real ish rejimida olinishi kerak.")),
    (_("Hujjatlarimiz uchinchi shaxsga beriladimi?"),
     _("Yoʻq. Hujjatlar faqat shartnoma doirasida ishlatiladi; axborot xavfsizligi tizimi ISO 27001:2022 "
       "boʻyicha sertifikatlangan.")),
]


def hero_title(site):
    """Hero sarlavhasi va uning indigo qismi; urgʻu faqat sarlavha bilan bir tilda boʻlsa olinadi."""
    lang = (translation.get_language() or "uz").split("-")[0]
    own_title = getattr(site, f"hero_title_{lang}", "")
    accent = getattr(site, f"hero_accent_{lang}", "") if own_title else site.hero_accent_uz
    return home_data.split_title(site.tr("hero_title"), accent)


def home(request):
    site = SiteSettings.load()
    title_main, title_accent = hero_title(site)
    context = {
        "title_main": title_main,
        "title_accent": title_accent,
        "facts": home_data.facts(site),
        "directions": Direction.objects.prefetch_related("services").all(),
        "credentials": Credential.objects.all(),
        "uzmap": maps.projects_map_context(Project.objects.all(), dept=request.GET.get(maps.DEPT_PARAM)),
        "team_strip": home_data.team_strip(),
        "sheet": home_data.sheet(),
        "slides": list(Slide.objects.filter(is_active=True)),
        "posts": Post.objects.filter(is_published=True)[:3],
        "faq": [{"q": q, "a": a} for q, a in HOME_FAQ],
    }
    context.update(compliance_context())
    return page(request, "core/home.html", **context)


def services(request):
    return page(
        request, "core/services.html", nav="services",
        crumbs=[(_("Xizmatlar"), None)],
        directions=Direction.objects.prefetch_related("services").all(),
    )


def direction(request, direction_slug):
    obj = get_object_or_404(Direction.objects.prefetch_related("services"), slug=direction_slug)
    is_energy = obj.accent == Direction.ACCENT_AMBER
    context = {
        "direction": obj,
        "is_energy": is_energy,
        "services": obj.services.all(),
        "legal_acts": obj.legal_acts.filter(verified_on__isnull=False),
        # Energoaudit ishlarining yili byulletenda yoʻq — ular ham chiqadi, yilsizlari oxirida
        "projects": obj.projects.order_by(F("year").desc(nulls_last=True), "order", "pk")[:6],
        "instruments": obj.instruments.all() if not is_energy else Instrument.objects.none(),
        "project_total": obj.projects.count(),
    }
    if is_energy:
        context.update(compliance_context())
        context.update(energy_context())
    return page(
        request, "core/direction.html", nav="services",
        crumbs=[(_("Xizmatlar"), reverse("core:services")), (obj.tr("title"), None)],
        **context,
    )


def service(request, direction_slug, slug):
    obj = get_object_or_404(Service.objects.select_related("direction"), direction__slug=direction_slug, slug=slug)
    return page(
        request, "core/service.html", nav="services",
        crumbs=[(_("Xizmatlar"), reverse("core:services")),
                (obj.direction.tr("title"), obj.direction.get_absolute_url()), (obj.tr("title"), None)],
        service=obj, direction=obj.direction,
        siblings=obj.direction.services.exclude(pk=obj.pk),
        legal_acts=obj.direction.legal_acts.filter(verified_on__isnull=False),
    )


def credentials(request):
    return page(
        request, "core/credentials.html", nav="credentials",
        crumbs=[(_("Hujjatlar"), None)],
        credentials=Credential.objects.all(),
    )


def instruments(request):
    return page(
        request, "core/instruments.html", nav="company",
        crumbs=[(_("Tashkilot"), reverse("core:company")), (_("Oʻlchov asboblari"), None)],
        instruments=Instrument.objects.all(),
    )


def company(request):
    return page(
        request, "core/company.html", nav="company",
        crumbs=[(_("Tashkilot"), None)],
        credentials=Credential.objects.all(),
        stats=Stat.objects.all(),
        leadership=TeamMember.objects.filter(is_leadership=True)[:4],
        # «Buyurtmachilar orasida» roʻyxati eski moliyaviy audit saytidan — mijoz tasdiqlaguncha chiqmaydi
    )


TEAM_DEPT_PARAM = "bolim"
TEAM_TABS = [("", _("Barchasi")), (TeamMember.DEPT_ENERGY, _("Energoaudit")),
             (TeamMember.DEPT_CONSTRUCTION, _("Qurilishda nazorat oʻlchovi"))]


def team(request):
    """Rahbariyat (direktor birinchi) va mutaxassislar; `?bolim=energy|construction` JS'siz tab."""
    members = TeamMember.objects.annotate(cert_count=Count("certificates"))
    specialists = members.filter(is_leadership=False)
    dept = request.GET.get(TEAM_DEPT_PARAM, "")
    if dept not in {TeamMember.DEPT_ENERGY, TeamMember.DEPT_CONSTRUCTION}:
        dept = ""
    counts = {key: specialists.filter(dept=key).count() for key, _label in TEAM_TABS if key}
    counts[""] = sum(counts.values())
    tabs = [{"key": key, "label": label, "count": counts[key], "active": key == dept,
             "url": (f"?{TEAM_DEPT_PARAM}={key}" if key else request.path) + "#mutaxassislar"}
            for key, label in TEAM_TABS]
    return page(
        request, "core/team.html", nav="team",
        crumbs=[(_("Jamoa"), None)],
        leadership=members.filter(is_leadership=True),
        specialists=specialists.filter(dept=dept) if dept else specialists,
        tabs=tabs,
        total=members.count(),
    )


def team_member(request, slug):
    member = get_object_or_404(TeamMember, slug=slug)
    # Oldingi/keyingi: jamoa sahifasidagi tartib (rahbariyat, keyin mutaxassislar — `order` boʻyicha)
    siblings = list(TeamMember.objects.only("slug", "full_name", "full_name_ru"))
    index = next(i for i, m in enumerate(siblings) if m.pk == member.pk)
    return page(
        request, "core/team_member.html", nav="team",
        crumbs=[(_("Jamoa"), reverse("core:team")), (member.display_name(), None)],
        member=member,
        certificates=member.certificates.all(),
        previous=siblings[index - 1] if index > 0 else None,
        next=siblings[index + 1] if index + 1 < len(siblings) else None,
    )


def requisites(request):
    return page(
        request, "core/requisites.html", nav="company",
        crumbs=[(_("Tashkilot"), reverse("core:company")), (_("Rekvizitlar"), None)],
    )


def legislation(request):
    return page(
        request, "core/legislation.html", nav="legislation",
        crumbs=[(_("Qonunchilik"), None)],
        acts=LegalAct.objects.filter(verified_on__isnull=False),
        posts=Post.objects.filter(is_published=True)[:4],
    )


def news(request):
    return page(
        request, "core/news.html", nav="news",
        crumbs=[(_("Yangiliklar"), None)],
        posts=Post.objects.filter(is_published=True).select_related("legal_act"),
    )


def post(request, slug):
    published = Post.objects.filter(is_published=True).select_related("legal_act")
    obj = get_object_or_404(published, slug=slug)
    return page(
        request, "core/post.html", nav="news",
        crumbs=[(_("Yangiliklar"), reverse("core:news")), (obj.tr("title"), None)],
        post=obj, others=published.exclude(pk=obj.pk)[:3],
    )


REGISTRY_PAGE_SIZE = 25


def registry(request):
    queryset = Project.objects.select_related("direction").order_by(F("year").desc(nulls_last=True), "order", "pk")
    direction_slug = request.GET.get("d", "")
    year = request.GET.get("y", "")
    year = year if year.isdigit() else ""
    query = request.GET.get("q", "").strip()
    region = request.GET.get(maps.REGION_PARAM, "")
    region = region if region in maps.REGIONS else ""
    if direction_slug:
        queryset = queryset.filter(direction__slug=direction_slug)
    if year:
        queryset = queryset.filter(year=int(year))
    if query:
        queryset = queryset.filter(Q(title_uz__icontains=query) | Q(title_ru__icontains=query) | Q(client__icontains=query))
    if region:
        queryset = queryset.filter(locations__region=region, locations__is_public=True, abroad=False).distinct()
    paginator = Paginator(queryset, REGISTRY_PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))
    return page(
        request, "core/registry.html", nav="registry",
        crumbs=[(_("Bajarilgan ishlar reestri"), None)],
        page_obj=page_obj, total=Project.objects.count(), found=paginator.count,
        directions=Direction.objects.all(),
        years=Project.objects.exclude(year__isnull=True).values_list("year", flat=True).distinct().order_by("-year"),
        active={"d": direction_slug, "y": year, "q": query, "hudud": region},
        regions=maps.region_options(),
        uzmap=maps.registry_map_context(request, direction_slug, region),
        offset=page_obj.start_index() - 1,
    )


def _wants_json(request) -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", "")


def contact(request):
    return page(request, "core/contact.html", nav="contact", crumbs=[(_("Aloqa"), None)], **form_context())


def request_page(request):
    context = {"hero_credentials": Credential.objects.filter(show_in_hero=True), "sent": request.GET.get("sent") == "1",
               "error": request.GET.get("error", "")}
    context.update(form_context())
    return page(request, "core/request.html", nav="contact", crumbs=[(_("Murojaat"), None)], **context)


@require_POST
def lead_create(request):
    """React formasi JSON kutadi; JS oʻchiq boʻlsa oddiy forma redirect oladi."""
    if not throttle.allow(f"lead:{throttle.client_ip(request)}", settings.LEAD_RATE_LIMIT, settings.LEAD_RATE_WINDOW_SECONDS):
        if _wants_json(request):
            return JsonResponse({"ok": False, "error": _("Juda koʻp soʻrov. Birozdan soʻng urinib koʻring yoki qoʻngʻiroq qiling.")}, status=429)
        return redirect(reverse("core:request") + "?error=limit")

    form = LeadForm(request.POST, request.FILES)
    if not form.is_valid():
        if _wants_json(request):
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        return redirect(reverse("core:request") + "?error=1")

    lead = form.save(commit=False)
    lead.language = request.LANGUAGE_CODE
    lead.source = (request.META.get("HTTP_REFERER") or "")[:200]
    lead.save()
    notify_telegram(lead)

    message = _("Murojaat qabul qilindi. Muhandis siz bilan bogʻlanadi.")
    if _wants_json(request):
        return JsonResponse({"ok": True, "message": message})
    return redirect(reverse("core:request") + "?sent=1")


def compliance_check(request):
    result = compliance.evaluate(
        object_kind=request.GET.get("object_kind", ""),
        area_m2=request.GET.get("area_m2"), annual_kwh=request.GET.get("annual_kwh"),
        annual_gas_m3=request.GET.get("annual_gas_m3"), estimate_value=request.GET.get("estimate_value"),
        funding=request.GET.get("funding", ""),
        has_dispute=request.GET.get("has_dispute") in ("1", "true", "on"),
    )
    payload = result.as_dict()
    slugs = {r["service_slug"] for r in payload["requirements"] if r["service_slug"]}
    urls = {s.slug: {"url": s.get_absolute_url(), "title": s.tr("title")}
            for s in Service.objects.select_related("direction").filter(slug__in=slugs)} if slugs else {}
    for item in payload["requirements"]:
        info = urls.get(item["service_slug"])
        if info:
            item["service_url"], item["service_title"] = info["url"], info["title"]
    return JsonResponse({"ok": True, **payload})


def energy_estimate(request):
    try:
        area = float(request.GET.get("area") or 0)
        kwh = float(request.GET.get("kwh") or 0)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": _("Notoʻgʻri qiymat")}, status=400)
    if not (math.isfinite(area) and math.isfinite(kwh)) or area < 0 or kwh < 0:
        return JsonResponse({"ok": False, "error": _("Notoʻgʻri qiymat")}, status=400)
    value = energy.specific_consumption(kwh, area)
    return JsonResponse({
        "ok": True, "specific": round(value, 1) if value is not None else None,
        "category": energy.category_for(value) if energy.BANDS_VERIFIED else None,
        "passport_required": energy.passport_required(area),
        "threshold": energy.PASSPORT_AREA_THRESHOLD_M2,
    })
