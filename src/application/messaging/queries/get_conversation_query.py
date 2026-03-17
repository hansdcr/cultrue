"""Get conversation query."""
from dataclasses import dataclass
from uuid import UUID

from src.application.messaging.dtos.conversation_dto import ConversationDTO
from src.domain.messaging.repositories.conversation_repository import ConversationRepository
from src.domain.messaging.value_objects.conversation_id import ConversationId
from src.domain.shared.exceptions import NotFoundException


@dataclass
class GetConversationQuery:
    """获取会话查询。"""
    conversation_id: UUID


class GetConversationQueryHandler:
    """获取会话查询处理器。"""

    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository

    async def handle(self, query: GetConversationQuery) -> ConversationDTO:
        """处理获取会话查询。

        Args:
            query: 查询

        Returns:
            ConversationDTO

        Raises:
            NotFoundException: 如果会话不存在
        """
        conversation_id = ConversationId(query.conversation_id)
        conversation = await self.conversation_repository.find_by_id(conversation_id)
        if not conversation:
            raise NotFoundException("Conversation not found")

        return ConversationDTO.from_entity(conversation)
