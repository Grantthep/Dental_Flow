"""users password_changed_at

Revision ID: 7c1d2e3f4a5b
Revises: 21eff677ad3c
Create Date: 2026-10-18 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c1d2e3f4a5b'
down_revision: Union[str, Sequence[str], None] = '21eff677ad3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'password_changed_at')
