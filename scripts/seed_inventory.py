import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.product import Product
from app.models.product_inventory import ProductInventory

def seed_inventory():
    app = create_app()
    with app.app_context():
        products = Product.query.all()
        seeded = 0
        for p in products:
            inv = ProductInventory.query.filter_by(product_id=p.id).first()
            if not inv:
                # Add 50 stock to test POS limits
                inv = ProductInventory(product_id=p.id, stock=50)
                db.session.add(inv)
                seeded += 1
            else:
                # Update to 50 if zero
                if inv.stock == 0:
                    inv.stock = 50
                    seeded += 1
        
        db.session.commit()
        print(f"\n📦 Inventario inicializado con exito: {seeded} productos actualizados a existencia = 50.")

if __name__ == "__main__":
    seed_inventory()
