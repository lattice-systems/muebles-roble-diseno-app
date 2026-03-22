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

    # Mail / SMTP
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in {"1", "true", "yes"}
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() in {"1", "true", "yes"}
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

    # Flask Security
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT")
    SECURITY_POST_LOGIN_VIEW = "/admin"
    SECURITY_TWO_FACTOR = True
    SECURITY_TWO_FACTOR_REQUIRED = False
    SECURITY_TWO_FACTOR_ENABLED_METHODS = ["authenticator"]
    SECURITY_TWO_FACTOR_RESCUE_EMAIL = False
    SECURITY_TWO_FACTOR_RESCUE_MAIL = os.getenv(
        "SECURITY_TWO_FACTOR_RESCUE_MAIL",
        "a59319001@smtp-brevo.com",
    )
    SECURITY_MULTI_FACTOR_RECOVERY_CODES = False
    SECURITY_EMAIL_SENDER = (
        os.getenv("SECURITY_EMAIL_SENDER") or MAIL_DEFAULT_SENDER or MAIL_USERNAME
    )
    SECURITY_TOTP_ISSUER = os.getenv("SECURITY_TOTP_ISSUER", "RobleDiseno")
    _security_totp_secret = os.getenv("SECURITY_TOTP_SECRET")
    if not _security_totp_secret:
        if os.getenv("FLASK_ENV") == "production":
            raise ValueError(
                "SECURITY_TOTP_SECRET must be set in production environment"
            )
        _security_totp_secret = "dev-totp-secret"
    SECURITY_TOTP_SECRETS = {"1": _security_totp_secret}
    SECURITY_MSG_EMAIL_NOT_PROVIDED = ("Debes ingresar tu correo electronico.", "error")
    SECURITY_MSG_INVALID_EMAIL_ADDRESS = (
        "El correo electronico no es valido.",
        "error",
    )
    SECURITY_MSG_PASSWORD_NOT_PROVIDED = ("Debes ingresar tu contrasena.", "error")
    SECURITY_MSG_USER_DOES_NOT_EXIST = ("El usuario no existe.", "error")
    SECURITY_MSG_INVALID_PASSWORD = ("La contrasena es incorrecta.", "error")
    SECURITY_MSG_LOGIN = ("Inicia sesion para acceder a esta pagina.", "info")
    SECURITY_MSG_CODE_HAS_BEEN_SENT = ("El codigo fue enviado.", "info")
    SECURITY_MSG_TWO_FACTOR_INVALID_TOKEN = (
        "El codigo de verificacion no es valido.",
        "error",
    )
    SECURITY_MSG_TWO_FACTOR_LOGIN_SUCCESSFUL = (
        "Tu codigo de verificacion fue confirmado.",
        "success",
    )
    SECURITY_MSG_TWO_FACTOR_SETUP_EXPIRED = (
        "La configuracion 2FA expiro. Inicia el proceso de nuevo.",
        "error",
    )
    SECURITY_MSG_TWO_FACTOR_METHOD_NOT_AVAILABLE = (
        "El metodo seleccionado no es valido para tu cuenta.",
        "error",
    )
    SECURITY_EMAIL_SUBJECT_TWO_FACTOR_RESCUE = (
        "Solicitud de recuperacion de autenticacion de dos factores"
    )

    if os.getenv("FLASK_ENV") == "production":
        missing = []
        for key in (
            "MAIL_SERVER",
            "MAIL_USERNAME",
            "MAIL_PASSWORD",
            "SECURITY_EMAIL_SENDER",
            "SECURITY_TWO_FACTOR_RESCUE_MAIL",
        ):
            if not locals().get(key):
                missing.append(key)
        if missing:
            raise ValueError(
                "Missing required mail/security configuration in production: "
                + ", ".join(missing)
            )

    # Have session and remember cookie be samesite (flask/flask_login)
    REMEMBER_COOKIE_SAMESITE = "strict"
    SESSION_COOKIE_SAMESITE = "strict"
