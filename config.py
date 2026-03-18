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

    # Have session and remember cookie be samesite (flask/flask_login)
    REMEMBER_COOKIE_SAMESITE = "strict"
    SESSION_COOKIE_SAMESITE = "strict"
