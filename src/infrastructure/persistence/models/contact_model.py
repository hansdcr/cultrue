"""Contact数据库模型。

定义contacts表的SQLAlchemy模型。
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.database import Base


class ContactModel(Base):
    """Contact模型。

    对应数据库中的contacts表。
    """

    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    contact_type: Mapped[str] = mapped_column(
        String(20), default="friend", index=True
    )
    alias: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    last_interaction_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        # 唯一约束：同一owner不能重复添加同一target
        UniqueConstraint("owner_id", "target_id", name="uq_contact_owner_target"),
    )

    def __repr__(self) -> str:
        """返回模型的字符串表示。

        Returns:
            模型的字符串表示
        """
        return f"<ContactModel(id={self.id}, owner_id={self.owner_id}, target_id={self.target_id})>"
