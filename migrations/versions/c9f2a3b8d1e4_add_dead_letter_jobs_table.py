"""add dead_letter_jobs table

Revision ID: c9f2a3b8d1e4
Revises: b8441ae972e5
Create Date: 2026-01-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'c9f2a3b8d1e4'
down_revision: Union[str, None] = 'b8441ae972e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'dead_letter_job',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('flow_run_id', sa.String(), nullable=False),
        sa.Column('flow_name', sa.String(), nullable=False),
        sa.Column('task_name', sa.String(), nullable=True),
        sa.Column('chapter_id', sa.String(), nullable=True),
        sa.Column('story_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('input_payload', JSONB(), nullable=False),
        sa.Column('error_type', sa.String(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('original_retry_count', sa.Integer(), nullable=False),
        sa.Column('failed_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapter.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['story_id'], ['story.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by'], ['user.id'], ondelete='SET NULL'),
    )
    
    # Indexes for common queries
    op.create_index('ix_dead_letter_job_flow_run_id', 'dead_letter_job', ['flow_run_id'])
    op.create_index('ix_dead_letter_job_status', 'dead_letter_job', ['status'])
    op.create_index('ix_dead_letter_job_flow_name', 'dead_letter_job', ['flow_name'])
    op.create_index('ix_dead_letter_job_user_id', 'dead_letter_job', ['user_id'])
    op.create_index('ix_dead_letter_job_failed_at', 'dead_letter_job', ['failed_at'])


def downgrade() -> None:
    op.drop_index('ix_dead_letter_job_failed_at', table_name='dead_letter_job')
    op.drop_index('ix_dead_letter_job_user_id', table_name='dead_letter_job')
    op.drop_index('ix_dead_letter_job_flow_name', table_name='dead_letter_job')
    op.drop_index('ix_dead_letter_job_status', table_name='dead_letter_job')
    op.drop_index('ix_dead_letter_job_flow_run_id', table_name='dead_letter_job')
    op.drop_table('dead_letter_job')
