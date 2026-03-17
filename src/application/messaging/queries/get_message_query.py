"""Get message query."""
from dataclasses import dataclass
from uuid import UUID

from src.application.messaging.dtos.message_dto import MessageDTO
from src.domain.messaging.repositories.message_repository import MessageRepository
from src.domain.messaging.value_objects.message_id import MessageId
from src.domain.shared.exceptions import NotFoundException


@dataclass
class GetMessageQuery:
    """获取消息查询。"""
    message_id: UUID


class GetMessageQueryHandler:
    """获取消息查询处理器。"""

    def __init__(self, message_repository: MessageRepository):
        self.message_repository = message_repository

    async def handle(self, query: GetMessageQuery) -> MessageDTO:
        """处理获取消息查询。

        Args:
            query: 查询

        Returns:
            MessageDTO

        Raises:
            NotFoundException: 如果消息不存在
        """
        message_id = MessageId(query.message_id)
        message = await self.message_repository.find_by_id(message_id)
        if not message:
            raise NotFoundException("Message not found")

        return MessageDTO.from_entity(message)
