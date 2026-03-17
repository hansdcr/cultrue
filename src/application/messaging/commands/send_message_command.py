"""Send message command."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.application.messaging.dtos.message_dto import MessageDTO
from src.application.shared.events.event_bus import EventBus
from src.domain.messaging.entities.message import Message
from src.domain.messaging.enums.message_type import MessageType
from src.domain.messaging.events.message_event import MessageEvent
from src.domain.messaging.repositories.conversation_repository import ConversationRepository
from src.domain.messaging.repositories.message_repository import MessageRepository
from src.domain.messaging.value_objects.conversation_id import ConversationId
from src.domain.shared.value_objects.actor import Actor
from src.domain.shared.exceptions import DomainException, NotFoundException


@dataclass
class SendMessageCommand:
    """发送消息命令。"""
    conversation_id: UUID
    sender: Actor           # 使用Actor值对象
    message_type: str
    content: str
    metadata: Optional[dict] = None


class SendMessageCommandHandler:
    """发送消息命令处理器。"""

    def __init__(
        self,
        message_repository: MessageRepository,
        conversation_repository: ConversationRepository,
        event_bus: EventBus = None  # 可选，用于发布事件
    ):
        self.message_repository = message_repository
        self.conversation_repository = conversation_repository
        self.event_bus = event_bus

    async def handle(self, command: SendMessageCommand) -> MessageDTO:
        """处理发送消息命令。

        Args:
            command: 发送命令

        Returns:
            MessageDTO

        Raises:
            NotFoundException: 如果会话不存在
            DomainException: 如果发送者不是会话成员
        """
        # 验证会话存在
        conversation_id = ConversationId(command.conversation_id)
        conversation = await self.conversation_repository.find_by_id(conversation_id)
        if not conversation:
            raise NotFoundException("Conversation not found")

        # 验证发送者是会话成员
        if not conversation.has_member(command.sender):
            raise DomainException("Sender is not a member of this conversation")

        # 解析消息类型
        message_type = MessageType(command.message_type)

        # 创建消息
        message = Message.create(
            conversation_id=conversation_id,
            sender=command.sender,
            content=command.content,
            message_type=message_type,
            metadata=command.metadata
        )

        # 保存消息
        saved_message = await self.message_repository.save(message)

        # 发布事件（异步推送）
        if self.event_bus:
            event = MessageEvent.from_message(saved_message, "message_sent")
            await self.event_bus.publish(event)

        return MessageDTO.from_entity(saved_message)

