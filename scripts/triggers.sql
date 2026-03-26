-- ============================================================
-- RF-VENT-01: Trigger de auditoría AFTER INSERT en sales
-- Ejecutar UNA SOLA VEZ en la base de datos:
--   mysql -u <user> -p <database> < scripts/triggers.sql
-- ============================================================

DELIMITER //

DROP TRIGGER IF EXISTS trg_sales_after_insert //

CREATE TRIGGER trg_sales_after_insert
AFTER INSERT ON sales
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (
        table_name,
        action,
        user_id,
        timestamp,
        previous_data,
        new_data
    )
    VALUES (
        'sales',
        'INSERT',
        NEW.id_employee,
        NOW(),
        NULL,
        JSON_OBJECT(
            'id',                NEW.id,
            'sale_date',         NEW.sale_date,
            'id_employee',       NEW.id_employee,
            'id_customer',       NEW.id_customer,
            'active',            NEW.active,
            'total',             NEW.total,
            'payment_method_id', NEW.payment_method_id
        )
    );
END //

DELIMITER ;

-- ============================================================
-- RF-VENT-02 & 04: Triggers de recálculo matemático AFTER INSERT, UPDATE, DELETE en sale_items
-- ============================================================

DELIMITER //

DROP TRIGGER IF EXISTS trg_sale_items_after_insert //
CREATE TRIGGER trg_sale_items_after_insert
AFTER INSERT ON sale_items
FOR EACH ROW
BEGIN
    UPDATE sales 
    SET total = (SELECT COALESCE(SUM(quantity * price), 0) FROM sale_items WHERE sale_id = NEW.sale_id)
    WHERE id = NEW.sale_id;
END //

DROP TRIGGER IF EXISTS trg_sale_items_after_update //
CREATE TRIGGER trg_sale_items_after_update
AFTER UPDATE ON sale_items
FOR EACH ROW
BEGIN
    -- Recalcular para el nuevo sale_id
    UPDATE sales 
    SET total = (SELECT COALESCE(SUM(quantity * price), 0) FROM sale_items WHERE sale_id = NEW.sale_id)
    WHERE id = NEW.sale_id;
    
    -- Recalcular para el antiguo sale_id en caso de cambio de cabecera
    IF OLD.sale_id != NEW.sale_id THEN
        UPDATE sales 
        SET total = (SELECT COALESCE(SUM(quantity * price), 0) FROM sale_items WHERE sale_id = OLD.sale_id)
        WHERE id = OLD.sale_id;
    END IF;
END //

DROP TRIGGER IF EXISTS trg_sale_items_after_delete //
CREATE TRIGGER trg_sale_items_after_delete
AFTER DELETE ON sale_items
FOR EACH ROW
BEGIN
    UPDATE sales 
    SET total = (SELECT COALESCE(SUM(quantity * price), 0) FROM sale_items WHERE sale_id = OLD.sale_id)
    WHERE id = OLD.sale_id;
END //

DELIMITER ;
