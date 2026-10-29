"""phase 3 decision records and approval updates

Revision ID: 002_phase3_schema
Revises: 001_initial_core
Create Date: 2026-10-29 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_phase3_schema'
down_revision: Union[str, None] = '001_initial_core'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add project_id to approval_requests
    with op.batch_alter_table('approval_requests') as batch_op:
        batch_op.add_column(sa.Column('project_id', sa.String(length=36), nullable=True))
        batch_op.create_index('ix_approval_requests_project_id', ['project_id'])
        batch_op.create_foreign_key(
            'fk_approval_requests_project_id',
            'projects',
            ['project_id'],
            ['id'],
            ondelete='SET NULL'
        )

    # 2. Create decision_records table
    op.create_table(
        'decision_records',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('task_id', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='ARCHITECTURE'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PROPOSED'),
        sa.Column('proposed_by', sa.String(length=64), nullable=False, server_default='archy'),
        sa.Column('reviewed_by', sa.String(length=64), nullable=True),
        sa.Column('approved_by', sa.String(length=64), nullable=True),
        sa.Column('decision', sa.Text(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('alternatives_considered', sa.JSON(), nullable=False),
        sa.Column('risks_identified', sa.JSON(), nullable=False),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_decision_records_id', 'decision_records', ['id'])
    op.create_index('ix_decision_records_project_id', 'decision_records', ['project_id'])
    op.create_index('ix_decision_records_task_id', 'decision_records', ['task_id'])
    op.create_index('ix_decision_records_category', 'decision_records', ['category'])
    op.create_index('ix_decision_records_status', 'decision_records', ['status'])
    op.create_index('ix_decision_records_proposed_by', 'decision_records', ['proposed_by'])
    op.create_index('ix_decision_records_reviewed_by', 'decision_records', ['reviewed_by'])


def downgrade() -> None:
    op.drop_table('decision_records')
    with op.batch_alter_table('approval_requests') as batch_op:
        batch_op.drop_constraint('fk_approval_requests_project_id', type_='foreignkey')
        batch_op.drop_index('ix_approval_requests_project_id')
        batch_op.drop_column('project_id')
