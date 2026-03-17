"""Message event."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from src.domain.shared.value_objects.actor import Actor


@dataclass
class MessageEvent:
    """消息事件。"""
    event_type: str  # "message_sent", "message_deleted", etc.
    message_id: UUID
    conversation_id: UUID
    sender: Actor
    content: str
    message_type: str
    metadata: Optional[dict]
    created_at: datetime

    @classmethod
    def from_message(cls, message, event_type: str = "message_sent") -> "MessageEvent":
        """从Message实体创建事件。

        Args:
            message: Message实体
            event_type: 事件类型

        Returns:
            MessageEvent实例
        """
        return cls(
            event_type=event_type,
            message_id=message.id,
            conversation_id=message.conversation_id,
            sender=message.sender,
            content=message.content,
            message_type=message.message_type.value,
            metadata=message.metadata,
            created_at=message.created_at
        )
