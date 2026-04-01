"""add_customer_order_fields_hu14

Revision ID: a1b2c3d4e5f6
Revises: 036150c66af6
Create Date: 2026-04-01 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '21d69f24b00e'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar nuevas columnas a la tabla orders
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('estimated_delivery_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('source', sa.String(length=20), nullable=False, server_default='manual'))
        batch_op.add_column(sa.Column('created_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('cancelled_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('cancelled_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('cancelled_reason', sa.Text(), nullable=True))
        batch_op.alter_column('status',
               existing_type=sa.String(length=50),
               nullable=False,
               existing_server_default=None,
               server_default='pendiente')
        batch_op.create_foreign_key(
            'fk_orders_created_by_id', 'users',
            ['created_by_id'], ['id']
        )
        batch_op.create_foreign_key(
            'fk_orders_cancelled_by_id', 'users',
            ['cancelled_by_id'], ['id']
        )

    # Agregar FK a production_orders para lanzar orden de cliente
    with op.batch_alter_table('production_orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('customer_order_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_production_orders_customer_order_id', 'orders',
            ['customer_order_id'], ['id']
        )


def downgrade():
    with op.batch_alter_table('production_orders', schema=None) as batch_op:
        batch_op.drop_constraint('fk_production_orders_customer_order_id', type_='foreignkey')
        batch_op.drop_column('customer_order_id')

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_constraint('fk_orders_cancelled_by_id', type_='foreignkey')
        batch_op.drop_constraint('fk_orders_created_by_id', type_='foreignkey')
        batch_op.drop_column('cancelled_reason')
        batch_op.drop_column('cancelled_by_id')
        batch_op.drop_column('cancelled_at')
        batch_op.drop_column('created_by_id')
        batch_op.drop_column('source')
        batch_op.drop_column('notes')
        batch_op.drop_column('estimated_delivery_date')
