"""Actor value object."""
from dataclasses import dataclass
from uuid import UUID
from src.domain.shared.enums.actor_type import ActorType


@dataclass(frozen=True)
class Actor:
    """Actor值对象，统一表示User或Agent。

    Actor是一个轻量级的值对象，用于在领域层统一表示User和Agent。
    在数据库层，使用Participant实体来保证数据完整性。
    """
    actor_type: ActorType
    actor_id: UUID

    @classmethod
    def from_user(cls, user_id: UUID) -> "Actor":
        """从User创建Actor。

        Args:
            user_id: 用户ID

        Returns:
            Actor实例
        """
        return cls(actor_type=ActorType.USER, actor_id=user_id)

    @classmethod
    def from_agent(cls, agent_id: UUID) -> "Actor":
        """从Agent创建Actor。

        Args:
            agent_id: Agent ID

        Returns:
            Actor实例
        """
        return cls(actor_type=ActorType.AGENT, actor_id=agent_id)

    def is_user(self) -> bool:
        """判断是否为User。

        Returns:
            如果是User返回True，否则返回False
        """
        return self.actor_type == ActorType.USER

    def is_agent(self) -> bool:
        """判断是否为Agent。

        Returns:
            如果是Agent返回True，否则返回False
        """
        return self.actor_type == ActorType.AGENT
