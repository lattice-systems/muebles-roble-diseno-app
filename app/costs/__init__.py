from flask import Blueprint

costs_bp = Blueprint("costs", __name__)

from . import routes  # noqa: E402,F401
