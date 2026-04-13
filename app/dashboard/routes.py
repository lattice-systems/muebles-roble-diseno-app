from flask import render_template, request
from flask_login import current_user
from flask_security import auth_required

from app.extensions import db
from app.models import AuditLog
from app.dashboard import dashboard_bp
from app.dashboard.services import DashboardService
from app.production.services import ProductionService


@dashboard_bp.route("/", methods=["GET"])
@auth_required()
def index():
    assignee_filter = request.args.get("production_assignee_id", "all").strip() or "all"

    assigned_user_id: int | None = None
    if assignee_filter != "all":
        try:
            assigned_user_id = int(assignee_filter)
        except (TypeError, ValueError):
            assignee_filter = "all"

    assignee_choices = [("all", "Todos los responsables")]
    assignee_choices.extend(
        [
            (str(user_id), label)
            for user_id, label in ProductionService.get_assignable_user_choices(
                include_user_id=assigned_user_id
            )
        ]
    )

    # Audit log access to sensitive financial dashboard
    if current_user.is_authenticated:
        log = AuditLog(
            user_id=current_user.id,
            table_name="dashboard",
            action="view",
            previous_data=None,
            new_data={
                "action": "User viewed dashboard layout and metrics",
                "production_assignee_filter": assignee_filter,
            },
        )
        db.session.add(log)
        db.session.commit()

    data = DashboardService.get_full_dashboard(assigned_user_id=assigned_user_id)

    return render_template(
        "admin/dashboard/index.html",
        data=data,
        production_assignee_filter=assignee_filter,
        production_assignee_choices=assignee_choices,
    )
