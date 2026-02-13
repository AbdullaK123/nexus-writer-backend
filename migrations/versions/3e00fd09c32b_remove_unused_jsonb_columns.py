"""remove_unused_jsonb_columns

Revision ID: 3e00fd09c32b
Revises: d2dfee7f270e
Create Date: 2026-02-13 23:51:18.355373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '3e00fd09c32b'
down_revision: Union[str, None] = 'd2dfee7f270e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove unused JSONB columns from Chapter and Story tables.
    
    All extraction data is now stored in MongoDB. These columns were:
    - Write-only (never read) for Chapter extractions
    - Completely unused for Story consolidations
    - line_edits now read from MongoDB only
    """
    # Chapter table - drop 6 unused JSONB columns
    op.drop_column('chapter', 'character_extraction')
    op.drop_column('chapter', 'plot_extraction')
    op.drop_column('chapter', 'world_extraction')
    op.drop_column('chapter', 'structure_extraction')
    op.drop_column('chapter', 'themes')
    op.drop_column('chapter', 'line_edits')
    op.drop_column('chapter', 'line_edits_generated_at')
    op.drop_column('chapter', 'line_edits_stale')
    
    # Story table - drop 5 dead columns
    op.drop_column('story', 'character_bios')
    op.drop_column('story', 'plot_threads')
    op.drop_column('story', 'world_bible')
    op.drop_column('story', 'pacing_structure')
    op.drop_column('story', 'story_timeline')


def downgrade() -> None:
    """Restore columns (empty - data not recoverable)."""
    # These columns can be added back but data is lost
    # Not implementing full restoration as this is a one-way migration
    pass
