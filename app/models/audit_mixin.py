"""
Mixin de auditoría reutilizable.

Agrega automáticamente las columnas de calidad a cualquier modelo:
  - created_at / updated_at / deactivated_at   (timestamps)
  - created_by / updated_by / deactivated_by   (FK → users.id)

Uso:
    class MiModelo(AuditMixin, db.Model):
        ...
"""

from sqlalchemy.orm import declared_attr

from ..extensions import db


class AuditMixin:
    """Mixin que agrega columnas de auditoría a cualquier modelo."""

    # ── Timestamps ────────────────────────────────────────────────────
    created_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )
    deactivated_at = db.Column(db.DateTime, nullable=True)

    # ── Foreign keys al usuario responsable ───────────────────────────
    # Se usa @declared_attr porque cada tabla necesita su propia
    # instancia de ForeignKey (no se puede compartir entre modelos).

    @declared_attr
    def created_by(cls):
        return db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    @declared_attr
    def updated_by(cls):
        return db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    @declared_attr
    def deactivated_by(cls):
        return db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # ── Helper para serialización ─────────────────────────────────────
    def _audit_dict(self) -> dict:
        """Retorna los campos de auditoría como dict para usar en to_dict()."""
        return {
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deactivated_at": (
                self.deactivated_at.isoformat() if self.deactivated_at else None
            ),
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "deactivated_by": self.deactivated_by,
        }
