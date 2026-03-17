"""Message repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.messaging.entities.message import Message
from src.domain.messaging.value_objects.conversation_id import ConversationId
from src.domain.messaging.value_objects.message_id import MessageId


class MessageRepository(ABC):
    """消息仓储接口。"""

    @abstractmethod
    async def save(self, message: Message) -> Message:
        """保存消息。

        Args:
            message: 消息实体

        Returns:
            保存后的消息实体
        """
        pass

    @abstractmethod
    async def find_by_id(self, message_id: MessageId) -> Optional[Message]:
        """根据ID查找消息。

        Args:
            message_id: 消息ID

        Returns:
            消息实体，如果不存在返回None
        """
        pass

    @abstractmethod
    async def find_by_conversation_id(
        self,
        conversation_id: ConversationId,
        limit: int = 50,
        offset: int = 0
    ) -> List[Message]:
        """查找会话的消息列表。

        Args:
            conversation_id: 会话ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            消息列表
        """
        pass

    @abstractmethod
    async def count_by_conversation_id(self, conversation_id: ConversationId) -> int:
        """统计会话的消息数量。

        Args:
            conversation_id: 会话ID

        Returns:
            消息数量
        """
        pass

    @abstractmethod
    async def delete(self, message_id: MessageId) -> None:
        """删除消息。

        Args:
            message_id: 消息ID
        """
        pass
