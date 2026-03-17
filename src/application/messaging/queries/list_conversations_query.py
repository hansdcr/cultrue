"""List conversations query."""
from dataclasses import dataclass
from typing import List

from src.application.messaging.dtos.conversation_dto import ConversationDTO
from src.domain.messaging.repositories.conversation_repository import ConversationRepository
from src.domain.shared.value_objects.actor import Actor


@dataclass
class ListConversationsQuery:
    """列出会话查询。"""
    actor: Actor
    limit: int = 20
    offset: int = 0


class ListConversationsQueryHandler:
    """列出会话查询处理器。"""

    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository

    async def handle(self, query: ListConversationsQuery) -> List[ConversationDTO]:
        """处理列出会话查询。

        Args:
            query: 查询

        Returns:
            ConversationDTO列表
        """
        conversations = await self.conversation_repository.find_by_actor(
            query.actor, limit=query.limit, offset=query.offset
        )

        return [ConversationDTO.from_entity(conv) for conv in conversations]
