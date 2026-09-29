from django.conf.urls.i18n import i18n_patterns
from django.contrib.sitemaps.views import sitemap
from django.db import connection
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

from core import react_admin
from core.media import lead_attachment, public_media, public_media_pattern
from core.sitemaps import SITEMAPS



@never_cache
def healthz(request):
    """Platforma healthcheck'i: ilova va baza javob beryapti."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("admin/", react_admin.panel, name="react_admin"),
    path("admin/api/session/", react_admin.session, name="react_admin_session"),
    path("admin/api/login/", react_admin.sign_in, name="react_admin_login"),
    path("admin/api/logout/", react_admin.sign_out, name="react_admin_logout"),
    path("admin/api/catalog/", react_admin.catalog, name="react_admin_catalog"),
    path("admin/api/resources/<slug:key>/", react_admin.resource, name="react_admin_resource"),
    path("admin/api/resources/<slug:key>/<int:pk>/", react_admin.record, name="react_admin_record"),
    path("admin-files/lead/<int:pk>/", lead_attachment, name="lead_attachment"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("robots.txt", TemplateView.as_view(template_name="core/robots.txt", content_type="text/plain")),
    # DEBUG va prodda bir xil: faqat PUBLIC_MEDIA_PREFIXES; leads/ va boshqalar 404
    re_path(public_media_pattern(), public_media, name="public_media"),
]

# Har bir til oʻz prefiksida: /uz/ /ru/ /en/
urlpatterns += i18n_patterns(
    path("", include("core.urls")),
    prefix_default_language=True,
)
