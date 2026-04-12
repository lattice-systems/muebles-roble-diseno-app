from __future__ import annotations

from urllib.parse import urlparse

import pyotp
from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.shared.security_logging import log_security_event

from . import customer_auth_bp
from .decorators import (
    PENDING_2FA_SETUP_SECRET_KEY,
    clear_pending_2fa,
    customer_auth_required,
    get_current_customer_user,
    get_pending_2fa_user,
    login_customer_user,
    logout_customer_user,
    pop_pending_2fa_next,
    set_pending_2fa,
)
from .services import CustomerAuthService


def _resolve_redirect_target(default_endpoint: str = "customer_auth.dashboard"):
    requested_target = (
        request.form.get("next") or request.args.get("next") or ""
    ).strip()
    if not requested_target:
        return redirect(url_for(default_endpoint))

    parsed_url = urlparse(requested_target)
    if parsed_url.scheme and parsed_url.netloc and parsed_url.netloc != request.host:
        return redirect(url_for(default_endpoint))

    if parsed_url.scheme in {"http", "https"}:
        safe_target = parsed_url.path or "/"
        if parsed_url.query:
            safe_target = f"{safe_target}?{parsed_url.query}"
        return redirect(safe_target)

    if requested_target.startswith("/"):
        return redirect(requested_target)

    return redirect(url_for(default_endpoint))


def _safe_customer_log(*, event_type: str, result: str, reason: str | None = None):
    try:
        user = get_current_customer_user()
        log_security_event(
            event_type=event_type,
            result=result,
            user_id=None,
            email_or_identifier=(user.email if user else request.form.get("email")),
            ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
            user_agent=request.headers.get("User-Agent"),
            reason=reason,
            context_data={
                "scope": "customer",
                "customer_user_id": user.id if user else None,
                "path": request.path,
                "method": request.method,
            },
            source="customer_auth",
            commit=True,
        )
    except Exception as exc:
        current_app.logger.warning("No se pudo registrar evento customer auth: %s", exc)


@customer_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    customer_user = get_current_customer_user()
    if customer_user:
        return redirect(url_for("customer_auth.dashboard"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        auth_user = CustomerAuthService.authenticate_customer(email, password)
        if not auth_user:
            flash("Correo o contraseña incorrectos.", "error")
            _safe_customer_log(
                event_type="auth.customer.login.failed",
                result="denied",
                reason="Credenciales inválidas",
            )
            return render_template("store/account/login.html")

        next_target = (
            request.form.get("next") or request.args.get("next") or ""
        ).strip()
        if CustomerAuthService.is_2fa_enabled(auth_user):
            set_pending_2fa(auth_user.id, next_target or None)
            flash(
                "Ingresa tu código de verificación para completar el inicio de sesión.",
                "info",
            )
            return redirect(url_for("customer_auth.login_2fa"))

        login_customer_user(auth_user.id)
        _safe_customer_log(
            event_type="auth.customer.login.success",
            result="success",
            reason="Inicio de sesión exitoso",
        )
        flash("Inicio de sesión exitoso.", "success")
        return _resolve_redirect_target(default_endpoint="customer_auth.dashboard")

    return render_template("store/account/login.html")


@customer_auth_bp.route("/login/2fa", methods=["GET", "POST"])
def login_2fa():
    pending_user = get_pending_2fa_user()
    if not pending_user:
        clear_pending_2fa()
        flash("Tu sesión de verificación expiró. Inicia sesión de nuevo.", "error")
        return redirect(url_for("customer_auth.login"))

    if request.method == "POST":
        token = (request.form.get("token") or "").strip()
        if CustomerAuthService.verify_totp_code(
            pending_user.tf_totp_secret or "", token
        ):
            login_customer_user(pending_user.id)
            next_target = pop_pending_2fa_next()
            _safe_customer_log(
                event_type="auth.customer.login.success",
                result="success",
                reason="Inicio de sesión exitoso con 2FA",
            )
            flash("Inicio de sesión verificado correctamente.", "success")
            if next_target:
                return redirect(next_target)
            return redirect(url_for("customer_auth.dashboard"))

        flash("Código de verificación inválido.", "error")
        _safe_customer_log(
            event_type="auth.customer.2fa.failed",
            result="denied",
            reason="Código TOTP inválido",
        )

    return render_template("store/account/login_2fa.html")


@customer_auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if get_current_customer_user():
        return redirect(url_for("customer_auth.dashboard"))

    if request.method == "POST":
        try:
            customer_user, _customer = CustomerAuthService.register_customer_account(
                first_name=request.form.get("first_name") or "",
                last_name=request.form.get("last_name") or "",
                email=request.form.get("email") or "",
                phone=request.form.get("phone") or "",
                password=request.form.get("password") or "",
            )
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("store/account/register.html")

        login_customer_user(customer_user.id)
        _safe_customer_log(
            event_type="auth.customer.register.success",
            result="success",
            reason="Registro de cuenta cliente",
        )
        flash("Cuenta creada correctamente.", "success")
        return redirect(url_for("customer_auth.dashboard"))

    return render_template("store/account/register.html")


@customer_auth_bp.route("/logout", methods=["POST"])
def logout():
    if get_current_customer_user():
        _safe_customer_log(
            event_type="auth.customer.logout",
            result="success",
            reason="Cierre de sesión de cliente",
        )
    logout_customer_user()
    return redirect(url_for("ecommerce.home"))


@customer_auth_bp.route("/dashboard", methods=["GET"])
@customer_auth_required
def dashboard():
    customer_user = get_current_customer_user()
    pagination = CustomerAuthService.get_orders_for_user(
        customer_user,
        page=1,
        per_page=5,
    )
    recent_reviews = CustomerAuthService.get_recent_reviews_for_user(
        customer_user,
        limit=4,
    )

    return render_template(
        "store/account/dashboard.html",
        customer_user=customer_user,
        customer=CustomerAuthService.get_linked_customer(customer_user),
        recent_orders=pagination.items,
        recent_reviews=recent_reviews,
        total_orders=pagination.total,
        total_reviews=len(customer_user.reviews),
    )


@customer_auth_bp.route("/profile", methods=["GET", "POST"])
@customer_auth_required
def profile():
    customer_user = get_current_customer_user()
    customer = CustomerAuthService.get_linked_customer(customer_user)

    if request.method == "POST":
        try:
            customer = CustomerAuthService.update_profile(customer_user, request.form)
            flash("Perfil actualizado correctamente.", "success")
            return redirect(url_for("customer_auth.profile"))
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template(
        "store/account/profile.html",
        customer_user=customer_user,
        customer=customer,
        has_2fa=CustomerAuthService.is_2fa_enabled(customer_user),
    )


@customer_auth_bp.route("/orders", methods=["GET"])
@customer_auth_required
def orders():
    customer_user = get_current_customer_user()
    page = request.args.get("page", 1, type=int) or 1
    pagination = CustomerAuthService.get_orders_for_user(
        customer_user,
        page=page,
        per_page=10,
    )

    return render_template(
        "store/account/orders.html",
        customer_user=customer_user,
        orders=pagination.items,
        pagination=pagination,
    )


@customer_auth_bp.route("/orders/<int:order_id>", methods=["GET"])
@customer_auth_required
def order_detail(order_id: int):
    customer_user = get_current_customer_user()
    order = CustomerAuthService.get_order_for_user(customer_user, order_id)
    if not order:
        abort(404)

    return render_template(
        "store/account/order_detail.html",
        customer_user=customer_user,
        order=order,
    )


@customer_auth_bp.route("/reviews/product/<int:product_id>", methods=["POST"])
@customer_auth_required
def review_product(product_id: int):
    customer_user = get_current_customer_user()
    rating = request.form.get("rating")
    review_text = request.form.get("review_text") or ""

    try:
        CustomerAuthService.upsert_review(
            customer_user=customer_user,
            product_id=product_id,
            rating=int(rating) if rating is not None else rating,
            review_text=review_text,
        )
        flash("Tu reseña fue guardada correctamente.", "success")
    except ValueError as exc:
        flash(str(exc), "error")

    return redirect(url_for("ecommerce.product", product_id=product_id))


@customer_auth_bp.route("/security/2fa/setup", methods=["GET", "POST"])
@customer_auth_required
def setup_2fa():
    customer_user = get_current_customer_user()

    if request.method == "POST":
        pending_secret = session.get(PENDING_2FA_SETUP_SECRET_KEY, "")
        token = (request.form.get("token") or "").strip()

        if not pending_secret:
            flash("Primero genera una nueva configuración de 2FA.", "error")
            return redirect(url_for("customer_auth.setup_2fa"))

        if not CustomerAuthService.verify_totp_code(pending_secret, token):
            flash("El código ingresado no es válido.", "error")
            return redirect(url_for("customer_auth.setup_2fa"))

        CustomerAuthService.enable_2fa(customer_user, pending_secret)
        session.pop(PENDING_2FA_SETUP_SECRET_KEY, None)
        session.modified = True
        flash("2FA activado correctamente.", "success")
        return redirect(url_for("customer_auth.profile"))

    pending_secret = session.get(PENDING_2FA_SETUP_SECRET_KEY)
    if not pending_secret:
        pending_secret = pyotp.random_base32()
        session[PENDING_2FA_SETUP_SECRET_KEY] = pending_secret
        session.modified = True

    issuer = current_app.config.get("SECURITY_TOTP_ISSUER", "RobleDiseno")
    provisioning_uri = CustomerAuthService.build_totp_uri(
        customer_user,
        pending_secret,
        f"{issuer} Ecommerce",
    )

    return render_template(
        "store/account/two_factor_setup.html",
        customer_user=customer_user,
        secret=pending_secret,
        provisioning_uri=provisioning_uri,
    )


@customer_auth_bp.route("/security/2fa/disable", methods=["POST"])
@customer_auth_required
def disable_2fa():
    customer_user = get_current_customer_user()
    CustomerAuthService.disable_2fa(customer_user)
    session.pop(PENDING_2FA_SETUP_SECRET_KEY, None)
    session.modified = True
    flash("2FA desactivado.", "success")
    return redirect(url_for("customer_auth.profile"))
