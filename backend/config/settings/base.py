from os import path
import dj_database_url
from environs import Env, EnvError
from furl import furl

BASE_DIR = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))

env = Env()
env.read_env(path.join(BASE_DIR, ".env"), recurse=False)

SECRET_KEY = env("SECRET_KEY", "v8sk33sy82!uw3ty=!jjv5vp7=s2phrzw(m(hrn^f7e_#1h2al")
DEBUG = env.bool("DEBUG", True)

INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [path.join(BASE_DIR, "client/dist")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

STATIC_URL = "/static/"
STATIC_ROOT = path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [path.join(BASE_DIR, "client/dist/static")]
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": path.join(BASE_DIR, "db.sqlite3"),
    }
}
DATABASES["default"].update(
    dj_database_url.config(
        env="DATABASE_URL",
        conn_max_age=env.int("DATABASE_CONN_MAX_AGE", 500),
        ssl_require="sslmode" not in furl(env("DATABASE_URL", "")).args,
    )
)

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
    "http://localhost:3000",
    "http://192.168.1.117:3000",
    "http://192.168.56.1:3000",
    "http://10.0.2.15:3000",
]

ALLOWED_HOSTS = ["*"]
if DEBUG:
    CORS_ORIGIN_ALLOW_ALL = True
    CSRF_TRUSTED_ORIGINS += env.list("CSRF_TRUSTED_ORIGINS", [])

MEDIA_ROOT = env("MEDIA_ROOT", path.join(BASE_DIR, "media"))
MEDIA_URL = "/media/"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

SITE_ID = 1