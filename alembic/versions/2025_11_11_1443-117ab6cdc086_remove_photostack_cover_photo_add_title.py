"""remove_photostack_cover_photo_add_title

Revision ID: 117ab6cdc086
Revises: bc1fce5b7bf8
Create Date: 2025-11-11 14:43:23.029356

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '117ab6cdc086'
down_revision: Union[str, Sequence[str], None] = 'bc1fce5b7bf8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add title column
    op.add_column('photo_stacks', sa.Column('title', sa.String(length=200), nullable=True))
    
    # Drop cover_photo_id column (SQLite doesn't support DROP COLUMN directly)
    # For SQLite, we need to recreate the table
    with op.batch_alter_table('photo_stacks', schema=None) as batch_op:
        batch_op.drop_column('cover_photo_id')


def downgrade() -> None:
    """Downgrade schema."""
    # Remove title column
    with op.batch_alter_table('photo_stacks', schema=None) as batch_op:
        batch_op.drop_column('title')
    
    # Re-add cover_photo_id column
    op.add_column('photo_stacks', sa.Column('cover_photo_id', sa.INTEGER(), nullable=True))
