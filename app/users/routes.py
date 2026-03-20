from flask import render_template

from app.users import users_bp


@users_bp.route("/", methods=["GET"])
def index():
    return render_template("admin/administration/users/index.html")
