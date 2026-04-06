from flask_mail import Mail
from flask_migrate import Migrate
from flask_security import Security
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from .security_mail import BrandedMailUtil

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
mail = Mail()
security = Security(mail_util_cls=BrandedMailUtil)
