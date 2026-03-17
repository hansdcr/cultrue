"""Delete message command."""
from dataclasses import dataclass
from uuid import UUID

from src.domain.messaging.repositories.message_repository import MessageRepository
from src.domain.messaging.value_objects.message_id import MessageId
from src.domain.shared.value_objects.actor import Actor
from src.domain.shared.exceptions import DomainException, NotFoundException


@dataclass
class DeleteMessageCommand:
    """删除消息命令。"""
    message_id: UUID
    actor: Actor  # 当前操作的Actor


class DeleteMessageCommandHandler:
    """删除消息命令处理器。"""

    def __init__(self, message_repository: MessageRepository):
        self.message_repository = message_repository

    async def handle(self, command: DeleteMessageCommand) -> None:
        """处理删除消息命令。

        Args:
            command: 删除命令

        Raises:
            NotFoundException: 如果消息不存在
            DomainException: 如果不是消息发送者
        """
        # 查找消息
        message_id = MessageId(command.message_id)
        message = await self.message_repository.find_by_id(message_id)
        if not message:
            raise NotFoundException("Message not found")

        # 验证是否为发送者
        if not message.is_from(command.actor):
            raise DomainException("Only the sender can delete this message")

        # 删除消息
        await self.message_repository.delete(message_id)
