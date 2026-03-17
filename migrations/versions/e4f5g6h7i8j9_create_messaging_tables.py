"""create_messaging_tables

Revision ID: e4f5g6h7i8j9
Revises: d3c4e5f6g7h8
Create Date: 2026-03-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e4f5g6h7i8j9'
down_revision: Union[str, Sequence[str], None] = 'd3c4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. 创建conversations表
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_type', sa.String(length=20), nullable=False, server_default='direct'),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_conversations_type', 'conversations', ['conversation_type'])
    op.create_index('idx_conversations_status', 'conversations', ['status'])
    op.create_index('idx_conversations_last_message_at', 'conversations', ['last_message_at'], postgresql_ops={'last_message_at': 'DESC'})

    # 2. 创建conversation_members表
    op.create_table(
        'conversation_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('participant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('last_read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_muted', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['participant_id'], ['participants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('conversation_id', 'participant_id', name='uq_conversation_member')
    )
    op.create_index('idx_conversation_members_conversation_id', 'conversation_members', ['conversation_id'])
    op.create_index('idx_conversation_members_participant_id', 'conversation_members', ['participant_id'])

    # 3. 创建messages表
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_type', sa.String(length=20), nullable=False, server_default='text'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['participants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_messages_sender_id', 'messages', ['sender_id'])
    op.create_index('idx_messages_created_at', 'messages', ['created_at'])

    # 4. 创建触发器：新增消息时自动更新conversation的message_count和last_message_at
    op.execute("""
        CREATE OR REPLACE FUNCTION increment_message_count()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE conversations
            SET message_count = message_count + 1,
                last_message_at = NEW.created_at,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.conversation_id;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_increment_message_count
        AFTER INSERT ON messages
        FOR EACH ROW
        EXECUTE FUNCTION increment_message_count();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # 删除触发器和函数
    op.execute("DROP TRIGGER IF EXISTS trigger_increment_message_count ON messages;")
    op.execute("DROP FUNCTION IF EXISTS increment_message_count();")

    # 删除表（按依赖顺序）
    op.drop_index('idx_messages_created_at', table_name='messages')
    op.drop_index('idx_messages_sender_id', table_name='messages')
    op.drop_index('idx_messages_conversation_id', table_name='messages')
    op.drop_table('messages')

    op.drop_index('idx_conversation_members_participant_id', table_name='conversation_members')
    op.drop_index('idx_conversation_members_conversation_id', table_name='conversation_members')
    op.drop_table('conversation_members')

    op.drop_index('idx_conversations_last_message_at', table_name='conversations')
    op.drop_index('idx_conversations_status', table_name='conversations')
    op.drop_index('idx_conversations_type', table_name='conversations')
    op.drop_table('conversations')
