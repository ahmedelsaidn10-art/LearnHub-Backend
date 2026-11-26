import os

import certifi

from dotenv import load_dotenv
from sqlalchemy.engine import URL

# Load local development settings from .env when present.
load_dotenv()


def _as_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def _database_uri() -> str:
    # A complete URL can still be supplied by a hosting provider.
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # TiDB uses MySQL compatibility and requires TLS for its public endpoint.
    tidb_host = os.getenv("TIDB_HOST")
    if tidb_host:
        return URL.create(
            drivername="mysql+mysqlconnector",
            username=os.getenv("TIDB_USER", ""),
            password=os.getenv("TIDB_PASSWORD", ""),
            host=tidb_host,
            port=int(os.getenv("TIDB_PORT", "4000")),
            database=os.getenv("TIDB_DATABASE", "learnhub_db"),
        ).render_as_string(hide_password=False)

    # Local MySQL development keeps using separate settings.
    return URL.create(
        drivername="mysql+mysqlconnector",
        username=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DATABASE", "learnhub_db"),
    ).render_as_string(hide_password=False)


class Config:
    APP_ENV = os.getenv("APP_ENV", "development").lower()
    DEBUG = _as_bool("FLASK_DEBUG", APP_ENV == "development")

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-jwt-change-me")

    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
            "ssl_ca": os.getenv("TIDB_SSL_CA") or certifi.where(),
        }
    } if os.getenv("TIDB_HOST") else {}

    OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    MAIL_FROM = os.getenv("MAIL_FROM", "")
    SMTP_USE_SSL = _as_bool("SMTP_USE_SSL", False)
    EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "smtp").strip().lower()
    BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
    MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "LearnHub")

    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_COOKIE_SECURE = _as_bool("JWT_COOKIE_SECURE", False)
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "Lax")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "30")) * 60

    CORS_ORIGINS = _csv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )

    @classmethod
    def validate(cls) -> None:
        if cls.APP_ENV == "production":
            if cls.SECRET_KEY == "dev-only-change-me":
                raise RuntimeError("Set SECRET_KEY in the production environment.")
            if cls.JWT_SECRET_KEY == "dev-only-jwt-change-me":
                raise RuntimeError("Set JWT_SECRET_KEY in the production environment.")
            if not cls.JWT_COOKIE_SECURE:
                raise RuntimeError("JWT_COOKIE_SECURE must be enabled in production.")
