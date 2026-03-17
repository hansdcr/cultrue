"""Archive conversation command."""
from dataclasses import dataclass
from uuid import UUID

from src.application.messaging.dtos.conversation_dto import ConversationDTO
from src.domain.messaging.enums.conversation_status import ConversationStatus
from src.domain.messaging.repositories.conversation_repository import ConversationRepository
from src.domain.messaging.value_objects.conversation_id import ConversationId
from src.domain.shared.exceptions import NotFoundException


@dataclass
class ArchiveConversationCommand:
    """归档会话命令。"""
    conversation_id: UUID


class ArchiveConversationCommandHandler:
    """归档会话命令处理器。"""

    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository

    async def handle(self, command: ArchiveConversationCommand) -> ConversationDTO:
        """处理归档会话命令。

        Args:
            command: 归档命令

        Returns:
            ConversationDTO

        Raises:
            NotFoundException: 如果会话不存在
        """
        # 查找会话
        conversation_id = ConversationId(command.conversation_id)
        conversation = await self.conversation_repository.find_by_id(conversation_id)
        if not conversation:
            raise NotFoundException("Conversation not found")

        # 归档会话
        conversation.status = ConversationStatus.ARCHIVED

        # 保存
        saved_conversation = await self.conversation_repository.save(conversation)

        return ConversationDTO.from_entity(saved_conversation)
