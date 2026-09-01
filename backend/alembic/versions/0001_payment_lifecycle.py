"""Add pending payment lifecycle fields and webhook event storage."""
from alembic import op
import sqlalchemy as sa

revision = "0001_payment_lifecycle"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("orders", sa.Column("expires_at", sa.DateTime(), nullable=True))
    op.create_index("ix_orders_status", "orders", ["status"])
    op.add_column("payments", sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"))
    op.create_table("payment_webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(length=150), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("event_id"))
    op.create_index("ix_payment_webhook_events_event_id", "payment_webhook_events", ["event_id"])

def downgrade():
    op.drop_index("ix_payment_webhook_events_event_id", table_name="payment_webhook_events")
    op.drop_table("payment_webhook_events")
    op.drop_column("payments", "attempt_number")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_column("orders", "expires_at")
