"""add events tables

Revision ID: 7a8b9c0d1e2f
Revises: ddc4296840f0
Create Date: 2025-12-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a8b9c0d1e2f'
down_revision: Union[str, None] = 'ddc4296840f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('parent_event_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('location_name', sa.String(length=200), nullable=True),
        sa.Column('gps_latitude', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('gps_longitude', sa.Numeric(precision=11, scale=8), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('modified_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_event_id'], ['events.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint('parent_event_id != id', name='valid_parent_event'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for events
    op.create_index('ix_events_id', 'events', ['id'])
    op.create_index('ix_events_user_id', 'events', ['user_id'])
    op.create_index('ix_events_parent_event_id', 'events', ['parent_event_id'])
    op.create_index('ix_events_dates', 'events', ['start_date', 'end_date'])
    
    # Create photo_events junction table (many-to-many)
    op.create_table(
        'photo_events',
        sa.Column('photo_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['photo_id'], ['photos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('photo_id', 'event_id')
    )
    
    # Create indexes for photo_events
    op.create_index('ix_photo_events_event_id', 'photo_events', ['event_id'])
    op.create_index('ix_photo_events_photo_id', 'photo_events', ['photo_id'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_photo_events_photo_id', table_name='photo_events')
    op.drop_index('ix_photo_events_event_id', table_name='photo_events')
    op.drop_index('ix_events_dates', table_name='events')
    op.drop_index('ix_events_parent_event_id', table_name='events')
    op.drop_index('ix_events_user_id', table_name='events')
    op.drop_index('ix_events_id', table_name='events')
    
    # Drop tables
    op.drop_table('photo_events')
    op.drop_table('events')
