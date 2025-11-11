"""add_timeline_indexes

Revision ID: bc1fce5b7bf8
Revises: 106636619401
Create Date: 2025-11-10 14:53:36.782461

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc1fce5b7bf8'
down_revision: Union[str, Sequence[str], None] = '106636619401'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add indexes for timeline queries."""
    # Add index on photos.taken_at for efficient timeline aggregation
    # This index is crucial for year/month/day/hour queries
    op.create_index(
        'ix_photos_taken_at',
        'photos',
        ['taken_at'],
        unique=False
    )
    
    # Composite index for visibility + taken_at queries
    # Optimizes timeline queries that filter by visibility
    op.create_index(
        'ix_photos_visibility_taken_at',
        'photos',
        ['visibility', 'taken_at'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema - Remove timeline indexes."""
    op.drop_index('ix_photos_visibility_taken_at', table_name='photos')
    op.drop_index('ix_photos_taken_at', table_name='photos')
