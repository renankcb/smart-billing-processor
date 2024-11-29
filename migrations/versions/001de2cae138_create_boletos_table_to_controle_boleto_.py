"""Create Boletos table to controle boleto generation process

Revision ID: 001de2cae138
Revises: b74585a291d4
Create Date: 2024-11-29 19:48:19.933750

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001de2cae138'
down_revision: Union[str, None] = 'b74585a291d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'boletos',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('debt_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('generated_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('notified_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('boletos')
