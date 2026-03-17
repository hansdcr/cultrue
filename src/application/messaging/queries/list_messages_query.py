"""List messages query."""
from dataclasses import dataclass
from typing import List
from uuid import UUID

from src.application.messaging.dtos.message_dto import MessageDTO
from src.domain.messaging.repositories.message_repository import MessageRepository
from src.domain.messaging.value_objects.conversation_id import ConversationId


@dataclass
class ListMessagesQuery:
    """列出消息查询。"""
    conversation_id: UUID
    limit: int = 50
    offset: int = 0


class ListMessagesQueryHandler:
    """列出消息查询处理器。"""

    def __init__(self, message_repository: MessageRepository):
        self.message_repository = message_repository

    async def handle(self, query: ListMessagesQuery) -> List[MessageDTO]:
        """处理列出消息查询。

        Args:
            query: 查询

        Returns:
            MessageDTO列表
        """
        conversation_id = ConversationId(query.conversation_id)
        messages = await self.message_repository.find_by_conversation_id(
            conversation_id, limit=query.limit, offset=query.offset
        )

        return [MessageDTO.from_entity(msg) for msg in messages]
