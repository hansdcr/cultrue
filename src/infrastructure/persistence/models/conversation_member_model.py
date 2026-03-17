"""ConversationMember数据库模型。

定义conversation_members表的SQLAlchemy模型。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.database import Base


class ConversationMemberModel(Base):
    """ConversationMember模型。

    对应数据库中的conversation_members表。
    关联会话和参与者。
    """

    __tablename__ = "conversation_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("participants.id", ondelete="CASCADE"),
        nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    last_read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_muted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    __table_args__ = (
        # 唯一约束：每个会话中的参与者只能有一条记录
        UniqueConstraint(
            "conversation_id",
            "participant_id",
            name="uq_conversation_member"
        ),
    )

    def __repr__(self) -> str:
        """返回模型的字符串表示。

        Returns:
            模型的字符串表示
        """
        return f"<ConversationMemberModel(id={self.id}, conversation_id={self.conversation_id}, participant_id={self.participant_id})>"

