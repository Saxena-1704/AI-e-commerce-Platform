"""Record the manually-added products.image_url column safely."""
from alembic import op
import sqlalchemy as sa

revision = "0002_product_image_url"
down_revision = "0001_payment_lifecycle"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("products")}

    if "image_url" not in columns:
        op.add_column("products", sa.Column("image_url", sa.String(length=500), nullable=True))


def downgrade():
    # The column may have existed before this revision was applied. Do not
    # remove user-managed data during a downgrade.
    pass
