"""Media fayllar: ommaviy papkalar va murojaat fayllarini faqat xodimga berish."""
import posixpath
import re

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.static import serve

from .models import Lead


def public_media_pattern() -> str:
    """`settings.PUBLIC_MEDIA_PREFIXES` dagi papkalar uchun URL regex (MEDIA_URL ostida)."""
    prefixes = "|".join(re.escape(prefix) for prefix in settings.PUBLIC_MEDIA_PREFIXES)
    return rf"^{re.escape(settings.MEDIA_URL.lstrip('/'))}(?P<path>(?:{prefixes})/.+)$"


def public_media(request, path):
    """Faqat ruxsat etilgan papkalardan fayl beradi.

    `serve()` yoʻlni normallashtiradi — `credentials/../leads/x` `leads/x` ga aylanadi,
    shuning uchun prefiks normallashtirilgan yoʻlda qayta tekshiriladi.
    """
    normalized = posixpath.normpath(path).lstrip("/")
    top = normalized.split("/", 1)[0]
    if top not in settings.PUBLIC_MEDIA_PREFIXES or "/" not in normalized:
        raise Http404
    return serve(request, normalized, document_root=settings.MEDIA_ROOT)


@staff_member_required(login_url="/admin/")
def lead_attachment(request, pk):
    """Murojaatga biriktirilgan faylni faqat admin xodimiga yuklab beradi."""
    lead = get_object_or_404(Lead, pk=pk)
    if not lead.attachment:
        raise Http404
    try:
        handle = lead.attachment.open("rb")
    except FileNotFoundError as exc:
        raise Http404 from exc
    return FileResponse(handle, as_attachment=True, filename=posixpath.basename(lead.attachment.name))
