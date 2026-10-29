"""initial core schema

Revision ID: 001_initial_core
Revises: 
Create Date: 2026-10-28 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_core'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. agents
    op.create_table(
        'agents',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('personality', sa.Text(), nullable=False),
        sa.Column('objectives', sa.JSON(), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('model_config_data', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='IDLE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('ix_agents_id', 'agents', ['id'])
    op.create_index('ix_agents_status', 'agents', ['status'])

    # 2. projects
    op.create_table(
        'projects',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PLANNING'),
        sa.Column('created_by', sa.String(length=64), nullable=True),
        sa.Column('objectives', sa.JSON(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('ix_projects_id', 'projects', ['id'])
    op.create_index('ix_projects_status', 'projects', ['status'])

    # 3. tasks
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=64), nullable=True),
        sa.Column('assigned_to', sa.String(length=64), nullable=True),
        sa.Column('parent_task_id', sa.String(length=36), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=True),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('priority', sa.String(length=50), nullable=False, server_default='MEDIUM'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('ix_tasks_id', 'tasks', ['id'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('ix_tasks_priority', 'tasks', ['priority'])
    op.create_index('ix_tasks_created_by', 'tasks', ['created_by'])
    op.create_index('ix_tasks_assigned_to', 'tasks', ['assigned_to'])
    op.create_index('ix_tasks_project_id', 'tasks', ['project_id'])
    op.create_index('ix_tasks_parent_task_id', 'tasks', ['parent_task_id'])

    # 4. messages
    op.create_table(
        'messages',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('sender_id', sa.String(length=64), nullable=False),
        sa.Column('receiver_id', sa.String(length=64), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False, server_default='REQUEST'),
        sa.Column('task_id', sa.String(length=36), sa.ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='SENT'),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('ix_messages_id', 'messages', ['id'])
    op.create_index('ix_messages_sender_id', 'messages', ['sender_id'])
    op.create_index('ix_messages_receiver_id', 'messages', ['receiver_id'])
    op.create_index('ix_messages_message_type', 'messages', ['message_type'])
    op.create_index('ix_messages_status', 'messages', ['status'])
    op.create_index('ix_messages_task_id', 'messages', ['task_id'])
    op.create_index('ix_messages_project_id', 'messages', ['project_id'])

    # 5. events
    op.create_table(
        'events',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('related_agent_id', sa.String(length=64), nullable=True),
        sa.Column('related_task_id', sa.String(length=36), nullable=True),
        sa.Column('related_project_id', sa.String(length=36), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('ix_events_id', 'events', ['id'])
    op.create_index('ix_events_event_type', 'events', ['event_type'])
    op.create_index('ix_events_source', 'events', ['source'])
    op.create_index('ix_events_related_agent_id', 'events', ['related_agent_id'])
    op.create_index('ix_events_related_task_id', 'events', ['related_task_id'])

    # 6. memories
    op.create_table(
        'memories',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('agent_id', sa.String(length=64), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('importance', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('ix_memories_id', 'memories', ['id'])
    op.create_index('ix_memories_agent_id', 'memories', ['agent_id'])
    op.create_index('ix_memories_type', 'memories', ['type'])

    # 7. approval_requests
    op.create_table(
        'approval_requests',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('requesting_agent_id', sa.String(length=64), nullable=False),
        sa.Column('task_id', sa.String(length=36), sa.ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('risk_level', sa.String(length=50), nullable=False, server_default='MEDIUM'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('approved_by', sa.String(length=64), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('ix_approval_requests_id', 'approval_requests', ['id'])
    op.create_index('ix_approval_requests_requesting_agent_id', 'approval_requests', ['requesting_agent_id'])
    op.create_index('ix_approval_requests_status', 'approval_requests', ['status'])

    # 8. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('action', sa.String(length=150), nullable=False),
        sa.Column('agent_id', sa.String(length=64), nullable=True),
        sa.Column('user_id', sa.String(length=64), nullable=True),
        sa.Column('task_id', sa.String(length=36), nullable=True),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('result', sa.String(length=100), nullable=True),
        sa.Column('approved_by', sa.String(length=64), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_agent_id', 'audit_logs', ['agent_id'])
    op.create_index('ix_audit_logs_task_id', 'audit_logs', ['task_id'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('approval_requests')
    op.drop_table('memories')
    op.drop_table('events')
    op.drop_table('messages')
    op.drop_table('tasks')
    op.drop_table('projects')
    op.drop_table('agents')
