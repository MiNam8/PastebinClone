"""added timezone to texts date columns

Revision ID: 5ee1b1a54109
Revises: 2006ba3ac50c
Create Date: 2025-06-05 17:35:29.929311

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5ee1b1a54109'
down_revision: Union[str, None] = '2006ba3ac50c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'texts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('hash_value', sa.String(), primary_key=True, nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expiration_date', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('texts')
