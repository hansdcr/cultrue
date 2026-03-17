"""Message entity."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.domain.messaging.enums.message_type import MessageType
from src.domain.messaging.value_objects.conversation_id import ConversationId
from src.domain.messaging.value_objects.message_id import MessageId
from src.domain.shared.value_objects.actor import Actor


@dataclass
class Message:
    """消息实体。

    消息由Actor发送，可以是User或Agent。
    """
    id: MessageId
    conversation_id: ConversationId
    sender: Actor
    message_type: MessageType
    content: str
    metadata: Optional[dict] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_from(self, actor: Actor) -> bool:
        """判断消息是否来自指定Actor。

        Args:
            actor: 要检查的Actor

        Returns:
            如果消息来自该Actor返回True，否则返回False
        """
        return self.sender == actor

    @classmethod
    def create(
        cls,
        conversation_id: ConversationId,
        sender: Actor,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[dict] = None
    ) -> "Message":
        """创建消息。

        Args:
            conversation_id: 会话ID
            sender: 发送者Actor
            content: 消息内容
            message_type: 消息类型，默认为TEXT
            metadata: 元数据，可选

        Returns:
            Message实例
        """
        return cls(
            id=MessageId.generate(),
            conversation_id=conversation_id,
            sender=sender,
            message_type=message_type,
            content=content,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
