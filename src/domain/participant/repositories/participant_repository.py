"""Participant repository interface."""
from abc import ABC, abstractmethod
from typing import Optional

from src.domain.participant.entities.participant import Participant
from src.domain.shared.value_objects.actor import Actor


class ParticipantRepository(ABC):
    """Participant仓储接口。"""

    @abstractmethod
    async def find_by_actor(self, actor: Actor) -> Optional[Participant]:
        """根据Actor查找Participant。

        Args:
            actor: Actor值对象

        Returns:
            Participant实例，如果不存在返回None
        """
        pass

    @abstractmethod
    async def find_or_create(self, actor: Actor) -> Participant:
        """查找或创建Participant（核心方法）。

        如果Participant不存在，则自动创建。
        这是仓储层的核心方法，确保Participant始终存在。

        Args:
            actor: Actor值对象

        Returns:
            Participant实例
        """
        pass

    @abstractmethod
    async def save(self, participant: Participant) -> Participant:
        """保存Participant。

        Args:
            participant: Participant实例

        Returns:
            保存后的Participant实例
        """
        pass
