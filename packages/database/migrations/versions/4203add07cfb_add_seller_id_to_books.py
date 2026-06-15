"""add_seller_id_to_books

Revision ID: 4203add07cfb
Revises:
Create Date: 2026-04-26 07:35:28.768214

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4203add07cfb"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 'with_template' ensures SQLite handles the recreation of the table
    with op.batch_alter_table("books") as batch_op:
        batch_op.add_column(sa.Column("seller_id", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("books") as batch_op:
        batch_op.drop_column("seller_id")
