"""Django settings — TTT Audit sayti (tttaudit.uz)."""
from pathlib import Path
import os

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
# Lokal monorepoda frontend backend bilan yonma-yon turadi. Docker build esa
# yig'ilgan bundle'ni BASE_DIR/frontend ichiga nusxalaydi.
FRONTEND_DIR = BASE_DIR / "frontend"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = BASE_DIR.parent / "frontend"

DEV_SECRET_KEY = "dev-only-not-for-production-change-me"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or DEV_SECRET_KEY
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
if not DEBUG and SECRET_KEY == DEV_SECRET_KEY:
    raise ImproperlyConfigured(
        "DJANGO_DEBUG=0 da DJANGO_SECRET_KEY muhit oʻzgaruvchisi majburiy (dev kaliti bilan prod ishga tushmaydi)."
    )
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]
# Railway / Render o'z domenini muhit o'zgaruvchisida beradi
PLATFORM_HOSTS = [
    os.environ[_var] for _var in ("RAILWAY_PUBLIC_DOMAIN", "RENDER_EXTERNAL_HOSTNAME") if os.environ.get(_var)
]
# Railway healthcheck shu Host sarlavhasi bilan keladi (docs.railway.com: healthchecks).
# Bu host faqat Railway ichki tarmogʻidan keladi; tashqi trafik edge orqali oʻz domeni bilan.
if os.environ.get("RAILWAY_ENVIRONMENT"):
    PLATFORM_HOSTS.append("healthcheck.railway.app")
ALLOWED_HOSTS += [host for host in PLATFORM_HOSTS if host not in ALLOWED_HOSTS]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.MaxBodySizeMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "core.sitetext.SiteTextMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "core.context_processors.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

if os.environ.get("DATABASE_URL"):
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.config(conn_max_age=600, ssl_require=False)
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Til: UZ birlamchi, RU to'liq, EN donor loyihalari uchun ---
LANGUAGE_CODE = "uz"
LANGUAGES = [
    ("uz", "Oʻzbekcha"),
    ("ru", "Русский"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True
USE_TZ = True
TIME_ZONE = "Asia/Tashkent"

STATIC_URL = "static/"
STATICFILES_DIRS = [FRONTEND_DIR / "dist"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
# Railway'da volume shu papkaga ulanadi (standart /app/media); boshqa yoʻl boʻlsa DJANGO_MEDIA_ROOT
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT") or BASE_DIR / "media")
# /media/ ostida faqat shu papkalar ommaga xizmat qilinadi (DEBUG va prodda bir xil).
# Qolganlari — xususan leads/ (mijoz yuklagan fayllar) — 404; ular faqat admin orqali yuklab olinadi.
PUBLIC_MEDIA_PREFIXES = ("credentials", "team", "instruments", "projects", "directions", "hero", "branding", "slides")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Mutlaq havolalar (sitemap, canonical, OG)
SITE_URL = os.environ.get("SITE_URL", "https://tttaudit.uz").rstrip("/")

# Murojaat bildirishnomasi (boʻsh boʻlsa yuborilmaydi)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Murojaat chegarasi: bitta IP dan soatiga
LEAD_RATE_LIMIT = 5
LEAD_RATE_WINDOW_SECONDS = 3600

# Faqat sarlavhani qayta yozadigan teskari proksi ortida yoqiladi (Railway, nginx)
TRUST_X_REAL_IP = os.environ.get("TRUST_X_REAL_IP", "0") == "1"

# Murojaat chegarasi hisoblagichi ishchilar (gunicorn worker) oʻrtasida umumiy boʻlishi uchun
# prodda (DATABASE_URL bor) DatabaseCache, lokal/testda LocMemCache.
if os.environ.get("DATABASE_URL"):
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.db.DatabaseCache", "LOCATION": "cache_table"}}
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Soʻrov formasi fayl chegarasi (25 MB)
LEAD_MAX_UPLOAD_BYTES = 25 * 1024 * 1024
LEAD_ALLOWED_EXTENSIONS = [".pdf", ".xlsx", ".xls", ".docx", ".doc", ".dwg", ".zip", ".rar", ".jpg", ".jpeg", ".png"]

# Soʻrov tanasi chegarasi: CSRF va forma tahlilidan oldin MaxBodySizeMiddleware tekshiradi
MAX_REQUEST_BODY_BYTES = LEAD_MAX_UPLOAD_BYTES + 2 * 1024 * 1024

DATA_UPLOAD_MAX_MEMORY_SIZE = LEAD_MAX_UPLOAD_BYTES + 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# --- Prodda xavfsizlik (DEBUG=0 bo'lganda yoqiladi) ---
if not DEBUG:
    # Lokal prod-rejim testi uchun DJANGO_SSL_REDIRECT=0 bilan o'chiriladi.
    SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SSL_REDIRECT", "1") == "1"
    # Platforma healthcheck'i ichki HTTP orqali keladi — unga 301 emas, 200 kerak
    SECURE_REDIRECT_EXEMPT = [r"^healthz$"]
    # HSTS ehtiyotkorlik bilan: domen faqat HTTPS ekani tasdiqlangach 31536000 ga koʻtariladi
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "3600"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get("DJANGO_HSTS_INCLUDE_SUBDOMAINS", "0") == "1"
    SECURE_HSTS_PRELOAD = os.environ.get("DJANGO_HSTS_PRELOAD", "0") == "1"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    CSRF_TRUSTED_ORIGINS = [
        origin.strip()
        for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
        if origin.strip()
    ]
    # *.up.railway.app domenida admin kirishi va formalar CSRF 403 bermasin
    CSRF_TRUSTED_ORIGINS += [
        f"https://{host}" for host in PLATFORM_HOSTS
        if host != "healthcheck.railway.app" and f"https://{host}" not in CSRF_TRUSTED_ORIGINS
    ]
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        },
    }
