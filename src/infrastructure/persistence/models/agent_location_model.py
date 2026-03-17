"""Agent地理位置数据库模型。

定义agent_locations表的SQLAlchemy模型。
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey,
    Integer, Numeric, String, Index
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geography

from src.infrastructure.persistence.database import Base


class AgentLocationModel(Base):
    """Agent地理位置模型。

    对应数据库中的agent_locations表。
    """

    __tablename__ = "agent_locations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    latitude: Mapped[float] = mapped_column(Numeric(10, 8), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(11, 8), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    location: Mapped[str | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="chk_latitude"
        ),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="chk_longitude"
        ),
        Index("idx_agent_locations_agent_id", "agent_id"),
        Index("idx_agent_locations_is_active", "is_active"),
        Index("idx_agent_locations_display_order", "display_order"),
        Index("idx_agent_locations_location_gist", "location", postgresql_using="gist"),
    )

    def __repr__(self) -> str:
        """返回模型的字符串表示。

        Returns:
            模型的字符串表示
        """
        return f"<AgentLocationModel(id={self.id}, agent_id={self.agent_id}, address={self.address})>"
