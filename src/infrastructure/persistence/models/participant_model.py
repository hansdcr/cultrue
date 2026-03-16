"""Participant数据库模型。

定义participants表的SQLAlchemy模型。
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.database import Base


class ParticipantModel(Base):
    """Participant模型。

    对应数据库中的participants表。
    用于保证数据完整性的中间表。
    """

    __tablename__ = "participants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    participant_type: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        # CHECK约束：确保类型和ID匹配
        CheckConstraint(
            "(participant_type = 'user' AND user_id IS NOT NULL AND agent_id IS NULL) OR "
            "(participant_type = 'agent' AND agent_id IS NOT NULL AND user_id IS NULL)",
            name="check_participant_type_id_match"
        ),
        # 唯一约束：每个User/Agent只有一个Participant记录
        UniqueConstraint("user_id", name="uq_participant_user_id"),
        UniqueConstraint("agent_id", name="uq_participant_agent_id"),
    )

    def __repr__(self) -> str:
        """返回模型的字符串表示。

        Returns:
            模型的字符串表示
        """
        return f"<ParticipantModel(id={self.id}, type={self.participant_type})>"
