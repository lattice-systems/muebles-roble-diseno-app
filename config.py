import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SECRET_KEY is required for session management and CSRF protection
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        # Only allow default in development; production must set SECRET_KEY
        if os.getenv("FLASK_ENV") == "production":
            raise ValueError("SECRET_KEY must be set in production environment")
        SECRET_KEY = "dev-secret-key-change-in-production"

    # Flask Security
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT")
    SECURITY_POST_LOGIN_VIEW = "/admin"
    SECURITY_TWO_FACTOR = True
    SECURITY_TWO_FACTOR_REQUIRED = True
    SECURITY_TWO_FACTOR_ENABLED_METHODS = ["authenticator"]
    SECURITY_TOTP_ISSUER = os.getenv("SECURITY_TOTP_ISSUER", "RobleDiseno")
    _security_totp_secret = os.getenv("SECURITY_TOTP_SECRET")
    if not _security_totp_secret:
        if os.getenv("FLASK_ENV") == "production":
            raise ValueError(
                "SECURITY_TOTP_SECRET must be set in production environment"
            )
        _security_totp_secret = "dev-totp-secret"
    SECURITY_TOTP_SECRETS = {"1": _security_totp_secret}

    # Have session and remember cookie be samesite (flask/flask_login)
    REMEMBER_COOKIE_SAMESITE = "strict"
    SESSION_COOKIE_SAMESITE = "strict"
