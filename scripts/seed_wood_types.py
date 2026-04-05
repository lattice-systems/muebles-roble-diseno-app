"""Seed idempotente de catalogo de tipos de madera."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import WoodType
from seed_dataset import WOOD_TYPES


def seed_wood_types() -> None:
    app = create_app()
    with app.app_context():
        created = 0
        updated = 0

        for item in WOOD_TYPES:
            existing = WoodType.query.filter_by(name=item["name"]).first()
            if existing:
                existing.description = item.get("description")
                existing.status = True
                updated += 1
                continue

            db.session.add(
                WoodType(
                    name=item["name"],
                    description=item.get("description"),
                    status=True,
                )
            )
            created += 1

        db.session.commit()

        print("\nSeed de tipos de madera ejecutado correctamente.")
        print(f"- Tipos de madera creados: {created}")
        print(f"- Tipos de madera actualizados: {updated}\n")


if __name__ == "__main__":
    seed_wood_types()
