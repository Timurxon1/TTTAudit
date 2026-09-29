"""TTT Audit React boshqaruv paneli uchun sessiyali, allowlist CRUD API."""

import json

from django import forms
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods, require_POST

from .models import (
    Branch, Client, Credential, Direction, Instrument, Lead, LegalAct, Post, Project,
    ProjectLocation, Service, SiteSettings, SiteText, Slide, StaffCertificate, Stat, TeamMember,
)


RESOURCES = {
    "settings": ("Sayt", "Sayt sozlamalari", SiteSettings, False, False, set()),
    "texts": ("Sayt", "Sayt matnlari", SiteText, False, False, {"key", "kind"}),
    "slides": ("Sayt", "Slaydlar", Slide, True, True, set()),
    "directions": ("Xizmatlar", "Audit yoʻnalishlari", Direction, True, True, set()),
    "services": ("Xizmatlar", "Xizmatlar", Service, True, True, set()),
    "legal-acts": ("Xizmatlar", "Qonunchilik", LegalAct, True, True, set()),
    "projects": ("Loyihalar", "Loyihalar", Project, True, True, set()),
    "locations": ("Loyihalar", "Loyiha manzillari", ProjectLocation, True, True, set()),
    "clients": ("Loyihalar", "Mijozlar", Client, True, True, set()),
    "team": ("Tashkilot", "Jamoa", TeamMember, True, True, set()),
    "staff-certificates": ("Tashkilot", "Xodim sertifikatlari", StaffCertificate, True, True, set()),
    "credentials": ("Tashkilot", "Litsenziya va hujjatlar", Credential, True, True, set()),
    "instruments": ("Tashkilot", "Oʻlchov asboblari", Instrument, True, True, set()),
    "branches": ("Tashkilot", "Filiallar", Branch, True, True, set()),
    "posts": ("Kontent", "Yangiliklar", Post, True, True, set()),
    "stats": ("Kontent", "Statistika", Stat, True, True, set()),
    "leads": ("Murojaatlar", "Kelgan murojaatlar", Lead, False, False,
              {"created_at", "source", "language"}),
}


def _auth(request):
    return request.user.is_authenticated and request.user.is_active and request.user.is_staff


def _denied():
    return JsonResponse({"detail": "Avval tizimga kiring."}, status=401)


def _config(key):
    config = RESOURCES.get(key)
    if not config:
        return None
    group, label, model, can_add, can_delete, excluded = config
    return {"key": key, "group": group, "label": label, "model": model,
            "can_add": can_add, "can_delete": can_delete, "excluded": excluded}


def _fields(config):
    model = config["model"]
    result = []
    for field in [*model._meta.fields, *model._meta.many_to_many]:
        if field.primary_key or not field.editable or field.auto_created or field.name in config["excluded"]:
            continue
        result.append(field)
    return result


def _field_type(field):
    if isinstance(field, (models.ImageField, models.FileField)):
        return "file"
    if isinstance(field, models.BooleanField):
        return "boolean"
    if isinstance(field, (models.TextField, models.JSONField)):
        return "textarea"
    if isinstance(field, models.DateTimeField):
        return "datetime-local"
    if isinstance(field, models.DateField):
        return "date"
    if isinstance(field, models.EmailField):
        return "email"
    if isinstance(field, (models.IntegerField, models.FloatField, models.DecimalField)):
        return "number"
    if field.many_to_many:
        return "multiselect"
    if field.many_to_one:
        return "select"
    return "text"


def _options(field):
    if field.choices:
        return [{"value": str(value), "label": str(label)} for value, label in field.flatchoices]
    if field.many_to_one or field.many_to_many:
        return [{"value": str(obj.pk), "label": str(obj)}
                for obj in field.remote_field.model.objects.all()[:500]]
    return []


def _schema(config):
    return [{
        "name": field.name,
        "label": str(field.verbose_name).capitalize(),
        "type": _field_type(field),
        "required": not field.blank and not isinstance(field, models.BooleanField),
        "help": str(field.help_text or ""),
        "options": _options(field),
        "accept": "image/*" if isinstance(field, models.ImageField) else "",
    } for field in _fields(config)]


def _value(obj, field):
    if field.many_to_many:
        return [str(pk) for pk in getattr(obj, field.name).values_list("pk", flat=True)]
    value = getattr(obj, field.name)
    if isinstance(field, (models.ImageField, models.FileField)):
        if isinstance(obj, Lead) and field.name == "attachment" and value:
            return f"/admin-files/lead/{obj.pk}/"
        return value.url if value else ""
    if isinstance(field, models.JSONField):
        return json.dumps(value, ensure_ascii=False, indent=2) if value is not None else ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if value is None:
        return ""
    if field.many_to_one:
        return str(getattr(obj, f"{field.name}_id") or "")
    return value


def _record(obj, config):
    return {"id": obj.pk, "label": str(obj),
            "values": {field.name: _value(obj, field) for field in _fields(config)}}


def _form_class(config):
    return forms.modelform_factory(config["model"], fields=[field.name for field in _fields(config)])


def panel(request):
    return render(request, "core/react_admin.html")


def session(request):
    return JsonResponse({"authenticated": _auth(request), "username": request.user.get_username() if _auth(request) else "",
                         "csrf": get_token(request)})


@require_POST
def sign_in(request):
    user = authenticate(request, username=request.POST.get("username", ""), password=request.POST.get("password", ""))
    if not user or not user.is_active or not user.is_staff:
        return JsonResponse({"detail": "Login yoki parol notoʻgʻri."}, status=400)
    login(request, user)
    return JsonResponse({"authenticated": True, "username": user.get_username(), "csrf": get_token(request)})


@require_POST
def sign_out(request):
    logout(request)
    return JsonResponse({"ok": True})


def catalog(request):
    if not _auth(request):
        return _denied()
    items = []
    for key in RESOURCES:
        config = _config(key)
        items.append({"key": key, "group": config["group"], "label": config["label"],
                      "count": config["model"].objects.count(), "canAdd": config["can_add"]})
    return JsonResponse({"items": items, "username": request.user.get_username()})


@require_http_methods(["GET", "POST"])
def resource(request, key):
    if not _auth(request):
        return _denied()
    config = _config(key)
    if not config:
        return JsonResponse({"detail": "Boʻlim topilmadi."}, status=404)
    if request.method == "POST":
        if not config["can_add"]:
            return JsonResponse({"detail": "Bu bo‘limda yangi yozuv yaratib bo‘lmaydi."}, status=403)
        form = _form_class(config)(request.POST, request.FILES)
        if not form.is_valid():
            return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
        obj = form.save()
        return JsonResponse({"record": _record(obj, config)}, status=201)

    queryset = config["model"].objects.all()
    query = request.GET.get("q", "").strip()
    if query:
        search = Q()
        for field in config["model"]._meta.fields:
            if isinstance(field, (models.CharField, models.TextField, models.EmailField)):
                search |= Q(**{f"{field.name}__icontains": query})
        queryset = queryset.filter(search)
    try:
        queryset = queryset.order_by("order", "pk")
    except Exception:
        queryset = queryset.order_by("-pk")
    page = Paginator(queryset, 40).get_page(request.GET.get("page", 1))
    return JsonResponse({"resource": {"key": key, "label": config["label"], "canAdd": config["can_add"],
                                       "canDelete": config["can_delete"], "schema": _schema(config)},
                         "records": [_record(obj, config) for obj in page.object_list],
                         "page": page.number, "pages": page.paginator.num_pages, "total": page.paginator.count})


@require_http_methods(["GET", "POST", "DELETE"])
def record(request, key, pk):
    if not _auth(request):
        return _denied()
    config = _config(key)
    if not config:
        return JsonResponse({"detail": "Boʻlim topilmadi."}, status=404)
    obj = get_object_or_404(config["model"], pk=pk)
    if request.method == "GET":
        return JsonResponse({"record": _record(obj, config), "schema": _schema(config)})
    if request.method == "DELETE":
        if not config["can_delete"]:
            return JsonResponse({"detail": "Bu yozuvni o‘chirib bo‘lmaydi."}, status=403)
        obj.delete()
        return JsonResponse({"ok": True})
    form = _form_class(config)(request.POST, request.FILES, instance=obj)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
    obj = form.save()
    return JsonResponse({"record": _record(obj, config)})
