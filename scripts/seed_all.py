"""
Script de inicialización de base de datos.

Crea todas las tablas desde los modelos, marca la migración como al día,
y siembra: roles, admin user, tipos de mueble, productos, inventario
y métodos de pago.

Uso:
    .venv\\Scripts\\python scripts/seed_all.py
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.role import Role
from app.models.user import User
from app.models.furniture_type import FurnitureType
from app.models.product import Product
from app.models.product_inventory import ProductInventory
from app.models.payment_method import PaymentMethod


def seed():
    app = create_app()
    with app.app_context():
        # ── 1. Crear todas las tablas ─────────────────────────────────
        print("\n🗄️  Creando tablas desde los modelos...")
        db.create_all()
        print("   ✅ Tablas creadas.\n")

        # ── 2. Stamp Alembic head ─────────────────────────────────────
        from flask_migrate import stamp
        try:
            stamp(revision="head")
            print("   ✅ Alembic stamp → head.\n")
        except Exception as e:
            print(f"   ⚠️  Stamp falló (OK si es primera vez): {e}\n")

        # ── 3. Roles ─────────────────────────────────────────────────
        print("👤 Sembrando roles...")
        roles_data = [
            {"name": "Administrador", "description": "Acceso total al sistema"},
            {"name": "Vendedor", "description": "Acceso al POS y ventas"},
            {"name": "Almacenista", "description": "Gestión de inventarios"},
        ]
        role_map = {}
        for r in roles_data:
            existing = Role.query.filter_by(name=r["name"]).first()
            if existing:
                print(f"  ⏭️  {r['name']} (ya existe)")
                role_map[r["name"]] = existing.id
            else:
                role = Role(name=r["name"], description=r["description"], status=True)
                db.session.add(role)
                db.session.flush()
                role_map[r["name"]] = role.id
                print(f"  ✅ {r['name']}")
        db.session.commit()

        # ── 4. Admin User ────────────────────────────────────────────
        print("\n🔐 Sembrando usuario admin...")
        admin_email = "admin@roble.com"
        existing_admin = User.query.filter_by(email=admin_email).first()
        if existing_admin:
            print(f"  ⏭️  {admin_email} (ya existe)")
        else:
            from flask_security.utils import hash_password
            admin = User(
                full_name="Administrador",
                email=admin_email,
                password_hash=hash_password("Admin123!"),
                role_id=role_map["Administrador"],
                status=True,
            )
            db.session.add(admin)
            db.session.commit()
            print(f"  ✅ {admin_email} / Admin123!")

        # ── 5. Tipos de mueble ───────────────────────────────────────
        print("\n📦 Sembrando tipos de mueble...")
        furniture_types_data = [
            {"name": "Silla", "description": "Sillas de todo tipo y estilo"},
            {"name": "Mesa", "description": "Mesas de comedor, centro y escritorio"},
            {"name": "Sofa", "description": "Sofas y sillones para sala"},
            {"name": "Cama", "description": "Camas individuales, matrimoniales y king"},
            {"name": "Estante", "description": "Libreros y estantes de pared"},
            {"name": "Armario", "description": "Armarios, roperos y vestidores"},
            {"name": "Escritorio", "description": "Escritorios para oficina y estudio"},
            {"name": "Comoda", "description": "Comodas y gaveteros"},
        ]
        type_map = {}
        for ft in furniture_types_data:
            existing = FurnitureType.query.filter_by(name=ft["name"]).first()
            if existing:
                type_map[ft["name"]] = existing.id
                print(f"  ⏭️  {ft['name']}")
            else:
                obj = FurnitureType(name=ft["name"], description=ft["description"], status=True)
                db.session.add(obj)
                db.session.flush()
                type_map[ft["name"]] = obj.id
                print(f"  ✅ {ft['name']}")
        db.session.commit()

        # ── 6. Productos + Inventario ────────────────────────────────
        print("\n🪑 Sembrando productos e inventario...")
        products_data = [
            {"sku": "SL-001", "name": "Silla Nordica Roble", "type": "Silla", "price": 1850, "stock": 25},
            {"sku": "SL-002", "name": "Silla Ejecutiva Pro", "type": "Silla", "price": 3200, "stock": 15},
            {"sku": "SL-003", "name": "Silla Infantil", "type": "Silla", "price": 650, "stock": 30},
            {"sku": "SL-004", "name": "Silla Thonet Clasica", "type": "Silla", "price": 1200, "stock": 20},
            {"sku": "MS-001", "name": "Mesa Comedor 6 Personas", "type": "Mesa", "price": 4500, "stock": 10},
            {"sku": "MS-002", "name": "Mesa de Centro Minimalista", "type": "Mesa", "price": 2100, "stock": 18},
            {"sku": "MS-003", "name": "Mesa Auxiliar Redonda", "type": "Mesa", "price": 980, "stock": 22},
            {"sku": "ES-001", "name": "Escritorio Esquinero L", "type": "Escritorio", "price": 3750, "stock": 8},
            {"sku": "ES-002", "name": "Escritorio Minimalista", "type": "Escritorio", "price": 2400, "stock": 12},
            {"sku": "SF-001", "name": "Sofa 3 Plazas Laguna", "type": "Sofa", "price": 8900, "stock": 5},
            {"sku": "SF-002", "name": "Sillon Individual Relax", "type": "Sofa", "price": 4200, "stock": 7},
            {"sku": "CB-001", "name": "Cama Matrimonial Arena", "type": "Cama", "price": 6500, "stock": 6},
            {"sku": "CB-002", "name": "Cama Individual Junior", "type": "Cama", "price": 3900, "stock": 10},
            {"sku": "CB-003", "name": "Cama King Avalon", "type": "Cama", "price": 11500, "stock": 4},
            {"sku": "LB-001", "name": "Librero Modular Oslo", "type": "Estante", "price": 3100, "stock": 14},
            {"sku": "AR-001", "name": "Armario 3 Puertas Sliding", "type": "Armario", "price": 9200, "stock": 3},
            {"sku": "CD-001", "name": "Comoda 6 Cajones Vintage", "type": "Comoda", "price": 4800, "stock": 9},
        ]
        seeded = 0
        for p in products_data:
            existing = Product.query.filter_by(sku=p["sku"]).first()
            if existing:
                print(f"  ⏭️  {p['sku']} – {p['name']}")
                # Ensure inventory exists
                inv = ProductInventory.query.filter_by(product_id=existing.id).first()
                if not inv:
                    db.session.add(ProductInventory(product_id=existing.id, stock=p["stock"]))
                    db.session.commit()
                continue

            ft_id = type_map.get(p["type"])
            if not ft_id:
                print(f"  ❌ Sin tipo '{p['type']}' para {p['sku']}")
                continue

            product = Product(
                sku=p["sku"], name=p["name"], furniture_type_id=ft_id,
                description=f"{p['name']} — mueble de alta calidad.",
                price=p["price"], status=True,
            )
            db.session.add(product)
            db.session.flush()

            inv = ProductInventory(product_id=product.id, stock=p["stock"])
            db.session.add(inv)
            db.session.commit()
            seeded += 1
            print(f"  ✅ {p['sku']} – {p['name']}  ${p['price']:,.0f}  (stock: {p['stock']})")

        print(f"   → {seeded} producto(s) creado(s).")

        # ── 7. Métodos de pago ───────────────────────────────────────
        print("\n💳 Sembrando métodos de pago...")
        pm_data = [
            {"name": "Efectivo", "type": "cash", "description": "Pago en efectivo"},
            {"name": "Tarjeta de Débito", "type": "debit_card", "description": "Pago con tarjeta de débito"},
            {"name": "Tarjeta de Crédito", "type": "credit_card", "description": "Pago con tarjeta de crédito"},
            {"name": "Transferencia", "type": "transfer", "description": "Transferencia bancaria / SPEI"},
        ]
        for pm in pm_data:
            existing = PaymentMethod.query.filter_by(name=pm["name"]).first()
            if existing:
                print(f"  ⏭️  {pm['name']}")
            else:
                obj = PaymentMethod(
                    name=pm["name"], type=pm["type"], description=pm["description"],
                    status=True, available_pos=True, available_ecommerce=True,
                )
                db.session.add(obj)
                print(f"  ✅ {pm['name']}")
        db.session.commit()

        print("\n✨ ¡Siembra completa! El sistema está listo.\n")
        print("   📌 Login: admin@roble.com / Admin123!\n")


if __name__ == "__main__":
    seed()
