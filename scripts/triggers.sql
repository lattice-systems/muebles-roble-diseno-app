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
