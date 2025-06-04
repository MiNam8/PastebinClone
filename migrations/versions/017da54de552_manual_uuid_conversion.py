"""manual_uuid_conversion

Revision ID: 017da54de552
Revises: f7d110ea3338
Create Date: 2025-05-22 19:47:43.903026

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '017da54de552'
down_revision: Union[str, None] = 'f7d110ea3338'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # First, add UUID extension if it doesn't exist
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # For table: users
    # 1. Add a temporary UUID column
    op.add_column('users', sa.Column('new_id', postgresql.UUID(), nullable=True))
    
    # 2. Fill it with UUIDs
    op.execute("UPDATE users SET new_id = uuid_generate_v4()")
    
    # 3. Make it non-nullable
    op.alter_column('users', 'new_id', nullable=False)
    
    # 4. Drop the primary key constraint
    op.drop_constraint('users_pkey', 'users', type_='primary')
    
    # 5. Drop the old id column
    op.drop_column('users', 'id')
    
    # 6. Rename new_id to id
    op.alter_column('users', 'new_id', new_column_name='id')
    
    # 7. Add primary key constraint
    op.create_primary_key('users_pkey', 'users', ['id'])
    
    # Repeat for table: items
    # 1. Add a temporary UUID column
    op.add_column('items', sa.Column('new_id', postgresql.UUID(), nullable=True))
    
    # 2. Fill it with UUIDs
    op.execute("UPDATE items SET new_id = uuid_generate_v4()")
    
    # 3. Make it non-nullable
    op.alter_column('items', 'new_id', nullable=False)
    
    # 4. Drop the primary key constraint
    op.drop_constraint('items_pkey', 'items', type_='primary')
    
    # 5. Drop the old id column
    op.drop_column('items', 'id')
    
    # 6. Rename new_id to id
    op.alter_column('items', 'new_id', new_column_name='id')
    
    # 7. Add primary key constraint
    op.create_primary_key('items_pkey', 'items', ['id'])


def downgrade() -> None:
    # Warning: This downgrade will lose the UUID information and generate new sequential IDs
    
    # For table: users
    op.drop_constraint('users_pkey', 'users', type_='primary')
    op.add_column('users', sa.Column('old_id', sa.Integer(), autoincrement=True, nullable=True))
    op.execute("UPDATE users SET old_id = nextval('users_id_seq')")
    op.alter_column('users', 'old_id', nullable=False)
    op.drop_column('users', 'id')
    op.alter_column('users', 'old_id', new_column_name='id')
    op.create_primary_key('users_pkey', 'users', ['id'])
    
    # For table: items
    op.drop_constraint('items_pkey', 'items', type_='primary')
    op.add_column('items', sa.Column('old_id', sa.Integer(), autoincrement=True, nullable=True))
    op.execute("UPDATE items SET old_id = nextval('items_id_seq')")
    op.alter_column('items', 'old_id', nullable=False)
    op.drop_column('items', 'id')
    op.alter_column('items', 'old_id', new_column_name='id')
    op.create_primary_key('items_pkey', 'items', ['id'])
