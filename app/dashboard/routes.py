from flask import render_template
from flask_login import current_user
from flask_security import auth_required

from app.extensions import db
from app.models import AuditLog
from app.dashboard import dashboard_bp
from app.dashboard.services import DashboardService


@dashboard_bp.route("/", methods=["GET"])
@auth_required()
def index():
    # Audit log access to sensitive financial dashboard
    if current_user.is_authenticated:
        log = AuditLog(
            user_id=current_user.id,
            table_name="dashboard",
            action="view",
            previous_data=None,
            new_data={"action": "User viewed dashboard layout and metrics"},
        )
        db.session.add(log)
        db.session.commit()

    data = DashboardService.get_full_dashboard()

    return render_template("admin/dashboard/index.html", data=data)
