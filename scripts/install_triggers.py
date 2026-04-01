import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

triggers_sql = [
    "DROP TRIGGER IF EXISTS trg_sale_items_after_insert",
    """
    CREATE TRIGGER trg_sale_items_after_insert
    AFTER INSERT ON sale_items
    FOR EACH ROW
    BEGIN
        UPDATE sales 
        SET total = (SELECT COALESCE(SUM(quantity * price), 0) FROM sale_items WHERE sale_id = NEW.sale_id)
        WHERE id = NEW.sale_id;
    END
    """,
    "DROP TRIGGER IF EXISTS trg_sale_items_after_update",
    """
    CREATE TRIGGER trg_sale_items_after_update
    AFTER UPDATE ON sale_items
    FOR EACH ROW
    BEGIN
        UPDATE sales 
        SET total = (SELECT COALESCE(SUM(quantity * price), 0) FROM sale_items WHERE sale_id = NEW.sale_id)
        WHERE id = NEW.sale_id;
        IF OLD.sale_id != NEW.sale_id THEN
            UPDATE sales 
            SET total = (SELECT COALESCE(SUM(quantity * price), 0) FROM sale_items WHERE sale_id = OLD.sale_id)
            WHERE id = OLD.sale_id;
        END IF;
    END
    """,
    "DROP TRIGGER IF EXISTS trg_sale_items_after_delete",
    """
    CREATE TRIGGER trg_sale_items_after_delete
    AFTER DELETE ON sale_items
    FOR EACH ROW
    BEGIN
        UPDATE sales 
        SET total = (SELECT COALESCE(SUM(quantity * price), 0) FROM sale_items WHERE sale_id = OLD.sale_id)
        WHERE id = OLD.sale_id;
    END
    """,
]

with app.app_context():
    try:
        for cmd in triggers_sql:
            db.session.execute(text(cmd))
        db.session.commit()
        print("Triggers installed successfully via SQLAlchemy.")
    except Exception as e:
        print(f"Failed to install triggers: {e}")
