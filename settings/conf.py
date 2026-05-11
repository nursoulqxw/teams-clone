from decouple import config, Csv

# ── Core ──────────────────────────────────────────────────────────────────────
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

# ── Database ──────────────────────────────────────────────────────────────────
DB_ENGINE = config("DB_ENGINE", default="django.db.backends.sqlite3")
DB_NAME = config("DB_NAME", default="db.sqlite3")
DB_USER = config("DB_USER", default="")
DB_PASSWORD = config("DB_PASSWORD", default="")
DB_HOST = config("DB_HOST", default="")
DB_PORT = config("DB_PORT", default="")

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_URL = config("REDIS_URL", default="redis://127.0.0.1:6379/1")

# ── JWT ───────────────────────────────────────────────────────────────────────
JWT_ACCESS_TOKEN_LIFETIME_MINUTES = config("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=60, cast=int)
JWT_REFRESH_TOKEN_LIFETIME_DAYS = config("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7, cast=int)
