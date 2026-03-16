"""Participant entity."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from src.domain.shared.enums.actor_type import ActorType
from src.domain.shared.value_objects.actor import Actor


@dataclass
class Participant:
    """Participant实体（数据库映射层）。

    用于保证数据完整性的中间表实体。
    应用层使用Actor，仓储层使用Participant。
    通过外键约束保证User和Agent的存在性。
    """
    id: UUID
    participant_type: ActorType
    user_id: Optional[UUID]
    agent_id: Optional[UUID]
    created_at: datetime

    @classmethod
    def from_actor(cls, actor: Actor) -> "Participant":
        """从Actor创建Participant。

        Args:
            actor: Actor值对象

        Returns:
            Participant实例
        """
        if actor.is_user():
            return cls(
                id=uuid4(),
                participant_type=ActorType.USER,
                user_id=actor.actor_id,
                agent_id=None,
                created_at=datetime.utcnow()
            )
        else:
            return cls(
                id=uuid4(),
                participant_type=ActorType.AGENT,
                user_id=None,
                agent_id=actor.actor_id,
                created_at=datetime.utcnow()
            )

    def to_actor(self) -> Actor:
        """转换为Actor。

        Returns:
            Actor值对象
        """
        if self.participant_type == ActorType.USER:
            return Actor.from_user(self.user_id)
        else:
            return Actor.from_agent(self.agent_id)
