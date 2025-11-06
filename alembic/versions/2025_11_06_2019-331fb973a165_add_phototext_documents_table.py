"""add_phototext_documents_table

Revision ID: 331fb973a165
Revises: 5d0677ce221a
Create Date: 2025-11-06 20:19:43.467951

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '331fb973a165'
down_revision: Union[str, Sequence[str], None] = '5d0677ce221a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create phototext_documents table
    op.create_table(
        'phototext_documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('content', JSONB, nullable=False),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('cover_image_hash', sa.String(length=64), nullable=True),
        sa.Column('cover_image_alt', sa.String(length=500), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.String(length=10), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "document_type IN ('general', 'album', 'slideshow')",
            name='valid_document_type'
        ),
        sa.CheckConstraint(
            "(cover_image_hash IS NULL AND cover_image_alt IS NULL) OR "
            "(cover_image_hash IS NOT NULL AND cover_image_alt IS NOT NULL)",
            name='valid_cover_image'
        ),
    )
    
    # Create indexes for performance
    op.create_index('ix_phototext_documents_id', 'phototext_documents', ['id'])
    op.create_index('ix_phototext_documents_user_id', 'phototext_documents', ['user_id'])
    op.create_index('ix_phototext_documents_document_type', 'phototext_documents', ['document_type'])
    op.create_index('ix_phototext_documents_is_published', 'phototext_documents', ['is_published'])
    op.create_index('ix_phototext_documents_created_at', 'phototext_documents', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    
    # Index for published documents (timeline view)
    op.create_index(
        'ix_phototext_documents_published',
        'phototext_documents',
        ['is_published', 'published_at'],
        postgresql_where=sa.text('is_published = true'),
        postgresql_ops={'published_at': 'DESC'}
    )
    
    # Full-text search index on title and abstract
    op.create_index(
        'ix_phototext_documents_search',
        'phototext_documents',
        [sa.text("to_tsvector('english', coalesce(title, '') || ' ' || coalesce(abstract, ''))")],
        postgresql_using='gin'
    )
    
    # JSON indexing for querying document content (using jsonb_path_ops operator class)
    op.execute(
        'CREATE INDEX ix_phototext_documents_content ON phototext_documents '
        'USING gin (content jsonb_path_ops)'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('ix_phototext_documents_content', table_name='phototext_documents')
    op.drop_index('ix_phototext_documents_search', table_name='phototext_documents')
    op.drop_index('ix_phototext_documents_published', table_name='phototext_documents')
    op.drop_index('ix_phototext_documents_created_at', table_name='phototext_documents')
    op.drop_index('ix_phototext_documents_is_published', table_name='phototext_documents')
    op.drop_index('ix_phototext_documents_document_type', table_name='phototext_documents')
    op.drop_index('ix_phototext_documents_user_id', table_name='phototext_documents')
    op.drop_index('ix_phototext_documents_id', table_name='phototext_documents')
    
    # Drop table
    op.drop_table('phototext_documents')

