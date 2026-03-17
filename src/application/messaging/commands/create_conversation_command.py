"""Create conversation command."""
from dataclasses import dataclass
from typing import List, Optional

from src.application.messaging.dtos.conversation_dto import ConversationDTO
from src.domain.messaging.entities.conversation import Conversation
from src.domain.messaging.enums.conversation_type import ConversationType
from src.domain.messaging.enums.conversation_status import ConversationStatus
from src.domain.messaging.repositories.conversation_repository import ConversationRepository
from src.domain.shared.value_objects.actor import Actor
from src.domain.shared.exceptions import DomainException


@dataclass
class CreateConversationCommand:
    """创建会话命令。"""
    conversation_type: str  # 'direct' or 'group'
    members: List[Actor]    # 使用Actor值对象
    title: Optional[str] = None
    creator: Optional[Actor] = None


class CreateConversationCommandHandler:
    """创建会话命令处理器。"""

    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository

    async def handle(self, command: CreateConversationCommand) -> ConversationDTO:
        """处理创建会话命令。

        Args:
            command: 创建命令

        Returns:
            ConversationDTO

        Raises:
            DomainException: 如果参数不合法
        """
        # 验证会话类型
        conversation_type = ConversationType(command.conversation_type)

        # 验证成员数量
        if conversation_type == ConversationType.DIRECT:
            if len(command.members) != 2:
                raise DomainException("Direct conversation must have exactly 2 members")

            # 检查Direct会话是否已存在
            existing = await self.conversation_repository.find_direct_conversation(
                command.members[0], command.members[1]
            )
            if existing and existing.status == ConversationStatus.ACTIVE:
                # 返回已存在的会话
                return ConversationDTO.from_entity(existing)

            # 创建Direct会话
            conversation = Conversation.create_direct(
                command.members[0], command.members[1]
            )
        else:
            # Group会话至少需要2个成员
            if len(command.members) < 2:
                raise DomainException("Group conversation must have at least 2 members")

            # 创建Group会话
            conversation = Conversation.create_group(
                command.title or "Group Chat", command.members
            )

        # 保存会话（仓储层会自动处理Participant）
        saved_conversation = await self.conversation_repository.save(conversation)

        return ConversationDTO.from_entity(saved_conversation)

