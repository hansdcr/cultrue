"""UserAgent数据库模型。

定义user_agents关联表的SQLAlchemy模型。
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.database import Base


class UserAgentModel(Base):
    """用户-Agent关联模型。

    对应数据库中的user_agents表，表示用户与Agent的关联关系。
    """

    __tablename__ = "user_agents"
    __table_args__ = (UniqueConstraint("user_id", "agent_id", name="uq_user_agent"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    last_interaction_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        """返回模型的字符串表示。

        Returns:
            模型的字符串表示
        """
        return f"<UserAgentModel(user_id={self.user_id}, agent_id={self.agent_id})>"
