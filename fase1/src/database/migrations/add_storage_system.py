"""Add storage system fields to import_sessions

Revision ID: add_storage_system
Revises: previous_migration
Create Date: 2024-10-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_storage_system'
down_revision = None  # Set this to the previous migration ID when integrated
branch_labels = None
depends_on = None


def upgrade():
    """Add storage system fields to import_sessions table"""
    # Add storage system columns
    op.add_column('import_sessions', sa.Column('storage_uuid', sa.String(36), nullable=True))
    op.add_column('import_sessions', sa.Column('storage_directory_name', sa.String(255), nullable=True))
    op.add_column('import_sessions', sa.Column('copy_status', sa.String(20), default='not_started', nullable=True))
    op.add_column('import_sessions', sa.Column('storage_size_mb', sa.Integer(), default=0, nullable=True))
    op.add_column('import_sessions', sa.Column('storage_started_at', sa.DateTime(), nullable=True))
    op.add_column('import_sessions', sa.Column('storage_completed_at', sa.DateTime(), nullable=True))
    
    # Set default values for existing records
    op.execute("UPDATE import_sessions SET copy_status = 'not_started' WHERE copy_status IS NULL")
    op.execute("UPDATE import_sessions SET storage_size_mb = 0 WHERE storage_size_mb IS NULL")
    
    # Create index on directory name for universal search
    op.create_index('ix_import_sessions_storage_directory_name', 'import_sessions', ['storage_directory_name'])


def downgrade():
    """Remove storage system fields from import_sessions table"""
    op.drop_index('ix_import_sessions_storage_directory_name')
    op.drop_column('import_sessions', 'storage_completed_at')
    op.drop_column('import_sessions', 'storage_started_at')
    op.drop_column('import_sessions', 'storage_size_mb')
    op.drop_column('import_sessions', 'copy_status')
    op.drop_column('import_sessions', 'storage_directory_name')
    op.drop_column('import_sessions', 'storage_uuid')