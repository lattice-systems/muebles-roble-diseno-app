"""
Script de siembra para usuarios base RBAC (1 usuario por rol canónico).

Uso:
    source venv/bin/activate
    python scripts/seed_users_by_role.py

Variables opcionales:
    SEED_RBAC_PASSWORD=RbacSeed#2026
    SEED_RBAC_RESET_PASSWORDS=true
"""

import os
import re
import sys
from typing import Any

from flask_security.utils import hash_password

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.role import Role
from app.models.user import User
from app.rbac import (
    ROLE_ADMIN,
    ROLE_CLIENT,
    ROLE_PRODUCTION,
    ROLE_SALES,
    ROLE_SUPERADMIN,
    resolve_role_key,
)

DEFAULT_PASSWORD = "RbacSeed#2026"

SEED_USERS: dict[str, dict[str, str]] = {
    ROLE_SUPERADMIN: {
        "role_name": "Super Administrador",
        "full_name": "Súper Administrador",
        "email": "superadmin@roble.com",
    },
    ROLE_ADMIN: {
        "role_name": "Administrador",
        "full_name": "Usuario Administrador",
        "email": "admin@roble.com",
    },
    ROLE_PRODUCTION: {
        "role_name": "Producción",
        "full_name": "Usuario Producción",
        "email": "produccion@roble.com",
    },
    ROLE_SALES: {
        "role_name": "Ventas",
        "full_name": "Usuario Ventas",
        "email": "ventas@roble.com",
    },
    ROLE_CLIENT: {
        "role_name": "Cliente",
        "full_name": "Usuario Cliente",
        "email": "cliente@roble.com",
    },
}

LEGACY_LOCAL_EMAILS: dict[str, str] = {
    ROLE_SUPERADMIN: "superadmin@roble.local",
    ROLE_ADMIN: "admin@roble.local",
    ROLE_PRODUCTION: "produccion@roble.local",
    ROLE_SALES: "ventas@roble.local",
    ROLE_CLIENT: "cliente@roble.local",
}


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise ValueError("SEED_RBAC_PASSWORD debe tener al menos 8 caracteres")
    if not re.search(r"[A-Z]", password):
        raise ValueError("SEED_RBAC_PASSWORD debe incluir al menos una mayúscula")
    if not re.search(r"[a-z]", password):
        raise ValueError("SEED_RBAC_PASSWORD debe incluir al menos una minúscula")
    if not re.search(r"\d", password):
        raise ValueError("SEED_RBAC_PASSWORD debe incluir al menos un número")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError(
            "SEED_RBAC_PASSWORD debe incluir al menos un carácter especial"
        )


def _get_canonical_roles() -> tuple[dict[str, Role], int]:
    role_by_key: dict[str, Role] = {}
    reactivated_roles = 0

    for role in Role.query.order_by(Role.id.asc()).all():
        role_key = resolve_role_key(role.name)
        if not role_key or role_key in role_by_key:
            continue

        if not role.status:
            role.status = True
            reactivated_roles += 1

        role_by_key[role_key] = role

    return role_by_key, reactivated_roles


def _upsert_user(
    role_key: str,
    seed_data: dict[str, str],
    role: Role,
    password: str,
    reset_passwords: bool,
) -> dict[str, Any]:
    email = seed_data["email"].strip().lower()
    full_name = seed_data["full_name"].strip()
    legacy_email = LEGACY_LOCAL_EMAILS.get(role_key, "").strip().lower()

    user = User.query.filter(User.email.ilike(email)).first()
    used_legacy_email = False
    if user is None and legacy_email and legacy_email != email:
        user = User.query.filter(User.email.ilike(legacy_email)).first()
        used_legacy_email = user is not None

    if user is None:
        db.session.add(
            User(
                full_name=full_name,
                email=email,
                password_hash=hash_password(password),
                role_id=role.id,
                status=True,
            )
        )
        return {
            "created": 1,
            "updated": 0,
            "password_reset": 0,
            "was_created": True,
            "migrated_email": 0,
        }

    changed = False
    migrated_email = 0
    if user.email.strip().lower() != email:
        user.email = email
        changed = True
        migrated_email = 1
    if user.full_name != full_name:
        user.full_name = full_name
        changed = True
    if user.role_id != role.id:
        user.role_id = role.id
        changed = True
    if not user.status:
        user.status = True
        changed = True

    password_reset = 0
    if reset_passwords:
        user.password_hash = hash_password(password)
        changed = True
        password_reset = 1

    return {
        "created": 0,
        "updated": 1 if changed else 0,
        "password_reset": password_reset,
        "was_created": False,
        "migrated_email": migrated_email if used_legacy_email or migrated_email else 0,
    }


def seed_users_by_role() -> None:
    password = os.getenv("SEED_RBAC_PASSWORD", DEFAULT_PASSWORD)
    reset_passwords = _is_truthy(os.getenv("SEED_RBAC_RESET_PASSWORDS"))

    _validate_password(password)
    app = create_app()

    with app.app_context():
        role_by_key, reactivated_roles = _get_canonical_roles()

        missing_roles: list[str] = []
        created = 0
        updated = 0
        password_reset = 0
        migrated_emails = 0
        user_password_map: dict[str, str] = {}

        for role_key, seed_data in SEED_USERS.items():
            role = role_by_key.get(role_key)
            if role is None:
                print(f"  + Creando rol canónico base faltante: {seed_data['role_name']}")
                role = Role(
                    name=seed_data["role_name"],
                    description=f"Rol de {seed_data['role_name']} autogenerado",
                    status=True
                )
                db.session.add(role)
                db.session.flush()
                role_by_key[role_key] = role

            result = _upsert_user(
                role_key=role_key,
                seed_data=seed_data,
                role=role,
                password=password,
                reset_passwords=reset_passwords,
            )
            created += result["created"]
            updated += result["updated"]
            password_reset += result["password_reset"]
            migrated_emails += result["migrated_email"]
            user_password_map[seed_data["role_name"]] = (
                password
                if result["was_created"] or reset_passwords
                else "[sin cambios]"
            )

        db.session.commit()

        print("\nRBAC seed ejecutado")
        print(f"- Roles reactivados: {reactivated_roles}")
        print(f"- Usuarios creados: {created}")
        print(f"- Usuarios actualizados: {updated}")
        print(f"- Passwords reseteados: {password_reset}")
        print(f"- Emails migrados (.local -> .com): {migrated_emails}")

        if missing_roles:
            missing_csv = ", ".join(missing_roles)
            print(f"- Roles faltantes (no se sembraron usuarios): {missing_csv}")

        print("\nCredenciales de seed:")
        for seed_data in SEED_USERS.values():
            print(
                f"  {seed_data['role_name']}: {seed_data['email']} / "
                f"{user_password_map.get(seed_data['role_name'], '[sin cambios]')}"
            )


if __name__ == "__main__":
    seed_users_by_role()
