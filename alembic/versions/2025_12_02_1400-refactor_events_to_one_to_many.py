"""refactor events to one-to-many

Revision ID: 3f4e5d6c7b8a
Revises: 7a8b9c0d1e2f
Create Date: 2025-12-02 14:00:00.000000

Refactors Events from many-to-many to one-to-many relationship.
- Drops photo_events junction table
- Adds event_id column to photos table
- Photos now belong to at most one event (simpler, clearer ownership)
- Collections and Tags already provide many-to-many functionality

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3f4e5d6c7b8a'
down_revision = '7a8b9c0d1e2f'
branch_labels = None
depends_on = None


def upgrade():
    """Refactor to one-to-many: add event_id to photos, drop photo_events"""
    
    # Drop photo_events junction table (no longer needed)
    op.drop_table('photo_events')
    
    # Add event_id column to photos table
    op.add_column('photos', sa.Column('event_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_photos_event_id',
        'photos', 'events',
        ['event_id'], ['id'],
        ondelete='SET NULL'  # If event deleted, photo remains but loses event association
    )
    
    # Add index for performance (filtering photos by event)
    op.create_index('ix_photos_event_id', 'photos', ['event_id'])


def downgrade():
    """Revert to many-to-many"""
    
    # Drop index
    op.drop_index('ix_photos_event_id', table_name='photos')
    
    # Drop foreign key
    op.drop_constraint('fk_photos_event_id', 'photos', type_='foreignkey')
    
    # Drop event_id column
    op.drop_column('photos', 'event_id')
    
    # Recreate photo_events junction table
    op.create_table(
        'photo_events',
        sa.Column('photo_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['photo_id'], ['photos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('photo_id', 'event_id')
    )
    
    # Recreate indexes
    op.create_index('ix_photo_events_photo_id', 'photo_events', ['photo_id'])
    op.create_index('ix_photo_events_event_id', 'photo_events', ['event_id'])
