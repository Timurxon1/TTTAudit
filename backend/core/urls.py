from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("xizmatlar/", views.services, name="services"),
    path("xizmatlar/<slug:direction_slug>/", views.direction, name="direction"),
    path("xizmatlar/<slug:direction_slug>/<slug:slug>/", views.service, name="service"),
    path("reestr/", views.registry, name="registry"),
    path("hujjatlar/", views.credentials, name="credentials"),
    path("qonunchilik/", views.legislation, name="legislation"),
    path("yangiliklar/", views.news, name="news"),
    path("yangiliklar/<slug:slug>/", views.post, name="post"),
    path("tashkilot/", views.company, name="company"),
    # eski manzil: /tashkilot/mutaxassislar/ -> /jamoa/ (301, shu tilda)
    path("tashkilot/mutaxassislar/", RedirectView.as_view(pattern_name="core:team", permanent=True,
                                                         query_string=True), name="team_legacy"),
    path("tashkilot/asboblar/", views.instruments, name="instruments"),
    path("tashkilot/rekvizitlar/", views.requisites, name="requisites"),
    path("jamoa/", views.team, name="team"),
    path("jamoa/<slug:slug>/", views.team_member, name="team_member"),
    path("aloqa/", views.contact, name="contact"),
    path("murojaat/", views.request_page, name="request"),
    path("api/lead/", views.lead_create, name="lead_create"),
    path("api/compliance/", views.compliance_check, name="compliance_check"),
    path("api/energy-estimate/", views.energy_estimate, name="energy_estimate"),
]
