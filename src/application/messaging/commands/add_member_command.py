"""Add member command."""
from dataclasses import dataclass
from uuid import UUID

from src.application.messaging.dtos.conversation_dto import ConversationDTO
from src.domain.messaging.repositories.conversation_repository import ConversationRepository
from src.domain.messaging.value_objects.conversation_id import ConversationId
from src.domain.shared.value_objects.actor import Actor
from src.domain.shared.exceptions import DomainException, NotFoundException


@dataclass
class AddMemberCommand:
    """添加成员命令。"""
    conversation_id: UUID
    member: Actor


class AddMemberCommandHandler:
    """添加成员命令处理器。"""

    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository

    async def handle(self, command: AddMemberCommand) -> ConversationDTO:
        """处理添加成员命令。

        Args:
            command: 添加命令

        Returns:
            ConversationDTO

        Raises:
            NotFoundException: 如果会话不存在
            DomainException: 如果是Direct会话或成员已存在
        """
        # 查找会话
        conversation_id = ConversationId(command.conversation_id)
        conversation = await self.conversation_repository.find_by_id(conversation_id)
        if not conversation:
            raise NotFoundException("Conversation not found")

        # Direct会话不能添加成员
        if conversation.is_direct():
            raise DomainException("Cannot add members to direct conversation")

        # 检查成员是否已存在
        if conversation.has_member(command.member):
            raise DomainException("Member already exists in conversation")

        # 添加成员
        conversation.add_member(command.member)

        # 保存
        saved_conversation = await self.conversation_repository.save(conversation)

        return ConversationDTO.from_entity(saved_conversation)
