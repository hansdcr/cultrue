"""Message DTO."""
from dataclasses import dataclass
from typing import Optional

from src.domain.messaging.entities.message import Message


@dataclass
class ActorInfo:
    """Actor信息。"""
    actor_type: str
    actor_id: str


@dataclass
class MessageDTO:
    """Message数据传输对象。"""
    id: str
    conversation_id: str
    sender: ActorInfo
    message_type: str
    content: str
    metadata: Optional[dict]
    created_at: str

    @classmethod
    def from_entity(cls, message: Message) -> "MessageDTO":
        """从Message实体创建DTO。

        Args:
            message: Message实体

        Returns:
            MessageDTO实例
        """
        return cls(
            id=str(message.id.value),
            conversation_id=str(message.conversation_id.value),
            sender=ActorInfo(
                actor_type=message.sender.actor_type.value,
                actor_id=str(message.sender.actor_id),
            ),
            message_type=message.message_type.value,
            content=message.content,
            metadata=message.metadata,
            created_at=message.created_at.isoformat(),
        )
