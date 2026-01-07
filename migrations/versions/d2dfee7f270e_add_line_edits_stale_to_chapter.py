"""add line_edits_stale to chapter

Revision ID: d2dfee7f270e
Revises: b8441ae972e5
Create Date: 2026-01-07 14:41:06.966551

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2dfee7f270e'
down_revision: Union[str, None] = 'b8441ae972e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add line_edits_stale column to chapter table."""
    op.add_column('chapter', sa.Column('line_edits_stale', sa.Boolean(), nullable=True))
    
    # Set default value to False for existing rows
    op.execute("UPDATE chapter SET line_edits_stale = false WHERE line_edits_stale IS NULL")


def downgrade() -> None:
    """Remove line_edits_stale column from chapter table."""
    op.drop_column('chapter', 'line_edits_stale')
