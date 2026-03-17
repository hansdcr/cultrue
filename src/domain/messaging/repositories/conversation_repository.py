"""Conversation repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.messaging.entities.conversation import Conversation
from src.domain.messaging.value_objects.conversation_id import ConversationId
from src.domain.shared.value_objects.actor import Actor


class ConversationRepository(ABC):
    """会话仓储接口。"""

    @abstractmethod
    async def save(self, conversation: Conversation) -> Conversation:
        """保存会话。

        Args:
            conversation: 会话实体

        Returns:
            保存后的会话实体
        """
        pass

    @abstractmethod
    async def find_by_id(self, conversation_id: ConversationId) -> Optional[Conversation]:
        """根据ID查找会话。

        Args:
            conversation_id: 会话ID

        Returns:
            会话实体，如果不存在返回None
        """
        pass

    @abstractmethod
    async def find_by_actor(
        self,
        actor: Actor,
        limit: int = 20,
        offset: int = 0
    ) -> List[Conversation]:
        """查找Actor参与的会话列表。

        Args:
            actor: Actor
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            会话列表
        """
        pass

    @abstractmethod
    async def find_direct_conversation(
        self,
        actor1: Actor,
        actor2: Actor
    ) -> Optional[Conversation]:
        """查找两个Actor之间的一对一会话。

        Args:
            actor1: 第一个Actor
            actor2: 第二个Actor

        Returns:
            会话实体，如果不存在返回None
        """
        pass

    @abstractmethod
    async def add_member(self, conversation_id: ConversationId, actor: Actor) -> None:
        """向会话添加成员。

        Args:
            conversation_id: 会话ID
            actor: 要添加的Actor
        """
        pass

    @abstractmethod
    async def remove_member(self, conversation_id: ConversationId, actor: Actor) -> None:
        """从会话移除成员。

        Args:
            conversation_id: 会话ID
            actor: 要移除的Actor
        """
        pass

    @abstractmethod
    async def update(self, conversation: Conversation) -> Conversation:
        """更新会话。

        Args:
            conversation: 会话实体

        Returns:
            更新后的会话实体
        """
        pass

    @abstractmethod
    async def delete(self, conversation_id: ConversationId) -> None:
        """删除会话。

        Args:
            conversation_id: 会话ID
        """
        pass
