"""add_participants_contacts_and_update_agents

Revision ID: d3c4e5f6g7h8
Revises: c27e259f13d4
Create Date: 2026-03-16 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd3c4e5f6g7h8'
down_revision: Union[str, Sequence[str], None] = 'c27e259f13d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. 添加api_key_prefix和api_key_hash字段到agents表
    op.add_column('agents', sa.Column('api_key_prefix', sa.String(length=16), nullable=True))
    op.add_column('agents', sa.Column('api_key_hash', sa.String(length=255), nullable=True))
    op.create_index('idx_agents_api_key_prefix', 'agents', ['api_key_prefix'])

    # 2. 创建participants表
    op.create_table(
        'participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('participant_type', sa.String(length=20), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "(participant_type = 'user' AND user_id IS NOT NULL AND agent_id IS NULL) OR "
            "(participant_type = 'agent' AND agent_id IS NOT NULL AND user_id IS NULL)",
            name='check_participant_type_id_match'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_participant_user_id'),
        sa.UniqueConstraint('agent_id', name='uq_participant_agent_id'),
    )
    op.create_index('idx_participants_type', 'participants', ['participant_type'])
    op.create_index('idx_participants_user_id', 'participants', ['user_id'])
    op.create_index('idx_participants_agent_id', 'participants', ['agent_id'])

    # 3. 创建contacts表
    op.create_table(
        'contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contact_type', sa.String(length=20), server_default='friend', nullable=False),
        sa.Column('alias', sa.String(length=100), nullable=True),
        sa.Column('is_favorite', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('last_interaction_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['participants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_id'], ['participants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_id', 'target_id', name='uq_contact_owner_target'),
    )
    op.create_index('idx_contacts_owner_id', 'contacts', ['owner_id'])
    op.create_index('idx_contacts_target_id', 'contacts', ['target_id'])
    op.create_index('idx_contacts_type', 'contacts', ['contact_type'])


def downgrade() -> None:
    """Downgrade schema."""
    # 删除contacts表
    op.drop_index('idx_contacts_type', table_name='contacts')
    op.drop_index('idx_contacts_target_id', table_name='contacts')
    op.drop_index('idx_contacts_owner_id', table_name='contacts')
    op.drop_table('contacts')

    # 删除participants表
    op.drop_index('idx_participants_agent_id', table_name='participants')
    op.drop_index('idx_participants_user_id', table_name='participants')
    op.drop_index('idx_participants_type', table_name='participants')
    op.drop_table('participants')

    # 删除agents表的新字段
    op.drop_index('idx_agents_api_key_prefix', table_name='agents')
    op.drop_column('agents', 'api_key_hash')
    op.drop_column('agents', 'api_key_prefix')
