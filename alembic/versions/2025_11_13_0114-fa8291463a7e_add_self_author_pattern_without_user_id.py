"""add_self_author_pattern_without_user_id

Revision ID: fa8291463a7e
Revises: 6a3e04989666
Create Date: 2025-11-13 01:14:24.511044

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa8291463a7e'
down_revision: Union[str, Sequence[str], None] = '6a3e04989666'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_self to authors and remove user_id (use batch mode for SQLite)
    with op.batch_alter_table('authors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_self', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.drop_index('ix_authors_user_id')
        batch_op.create_index(batch_op.f('ix_authors_is_self'), ['is_self'], unique=False)
        # SQLite batch mode will recreate table without foreign key automatically
        batch_op.drop_column('user_id')
    
    # Add default_author_id to users (use batch mode for SQLite)
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('default_author_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_users_default_author_id'), ['default_author_id'], unique=False)
        batch_op.create_foreign_key('fk_users_default_author', 'authors', ['default_author_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_default_author', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_users_default_author_id'))
        batch_op.drop_column('default_author_id')
    
    with op.batch_alter_table('authors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.INTEGER(), nullable=False))
        batch_op.create_foreign_key('fk_authors_user', 'users', ['user_id'], ['id'])
        batch_op.drop_index(batch_op.f('ix_authors_is_self'))
        batch_op.create_index('ix_authors_user_id', ['user_id'], unique=False)
        batch_op.drop_column('is_self')
