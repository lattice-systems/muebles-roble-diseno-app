import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
from app import create_app
from app.extensions import db
from app.models.product_inventory import ProductInventory
from app.models.product import Product

app = create_app()
with app.app_context():
    products = Product.query.all()
    print("Products without inventory:")
    for p in products:
        inv = ProductInventory.query.filter_by(product_id=p.id).first()
        if not inv:
            print(f"- {p.id}: {p.name} HAS NO INVENTORY RECORD")
        else:
            print(f"- {p.id}: {p.name} -> STOCK: {inv.stock}")
