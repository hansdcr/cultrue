"""Remove member command."""
from dataclasses import dataclass
from uuid import UUID

from src.application.messaging.dtos.conversation_dto import ConversationDTO
from src.domain.messaging.repositories.conversation_repository import ConversationRepository
from src.domain.messaging.value_objects.conversation_id import ConversationId
from src.domain.shared.value_objects.actor import Actor
from src.domain.shared.exceptions import DomainException, NotFoundException


@dataclass
class RemoveMemberCommand:
    """移除成员命令。"""
    conversation_id: UUID
    member: Actor


class RemoveMemberCommandHandler:
    """移除成员命令处理器。"""

    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository

    async def handle(self, command: RemoveMemberCommand) -> ConversationDTO:
        """处理移除成员命令。

        Args:
            command: 移除命令

        Returns:
            ConversationDTO

        Raises:
            NotFoundException: 如果会话不存在
            DomainException: 如果是Direct会话或成员不存在
        """
        # 查找会话
        conversation_id = ConversationId(command.conversation_id)
        conversation = await self.conversation_repository.find_by_id(conversation_id)
        if not conversation:
            raise NotFoundException("Conversation not found")

        # Direct会话不能移除成员
        if conversation.is_direct():
            raise DomainException("Cannot remove members from direct conversation")

        # 检查成员是否存在
        if not conversation.has_member(command.member):
            raise DomainException("Member not found in conversation")

        # 移除成员
        conversation.remove_member(command.member)

        # 保存
        saved_conversation = await self.conversation_repository.save(conversation)

        return ConversationDTO.from_entity(saved_conversation)
