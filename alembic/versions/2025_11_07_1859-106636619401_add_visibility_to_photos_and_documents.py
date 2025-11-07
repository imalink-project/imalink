"""add_visibility_to_photos_and_documents

Revision ID: 106636619401
Revises: 331fb973a165
Create Date: 2025-11-07 18:59:54.431518

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '106636619401'
down_revision: Union[str, Sequence[str], None] = '331fb973a165'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add visibility field to photos and phototext_documents."""
    # Add visibility column to photos table
    op.add_column('photos', 
        sa.Column('visibility', sa.String(length=20), nullable=False, server_default='private')
    )
    op.create_index(op.f('ix_photos_visibility'), 'photos', ['visibility'], unique=False)
    
    # Add CHECK constraint for photos.visibility
    op.create_check_constraint(
        'valid_photo_visibility',
        'photos',
        "visibility IN ('private', 'public')"
    )
    
    # Add visibility column to phototext_documents table
    op.add_column('phototext_documents',
        sa.Column('visibility', sa.String(length=20), nullable=False, server_default='private')
    )
    op.create_index(op.f('ix_phototext_documents_visibility'), 'phototext_documents', ['visibility'], unique=False)
    
    # Add CHECK constraint for phototext_documents.visibility
    op.create_check_constraint(
        'valid_document_visibility',
        'phototext_documents',
        "visibility IN ('private', 'public')"
    )


def downgrade() -> None:
    """Downgrade schema - Remove visibility fields."""
    # Drop phototext_documents visibility
    op.drop_constraint('valid_document_visibility', 'phototext_documents', type_='check')
    op.drop_index(op.f('ix_phototext_documents_visibility'), table_name='phototext_documents')
    op.drop_column('phototext_documents', 'visibility')
    
    # Drop photos visibility
    op.drop_constraint('valid_photo_visibility', 'photos', type_='check')
    op.drop_index(op.f('ix_photos_visibility'), table_name='photos')
    op.drop_column('photos', 'visibility')
