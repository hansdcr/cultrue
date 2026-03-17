"""Conversation DTO."""
from dataclasses import dataclass
from typing import List, Optional

from src.domain.messaging.entities.conversation import Conversation


@dataclass
class ActorInfo:
    """Actor信息。"""
    actor_type: str
    actor_id: str


@dataclass
class ConversationDTO:
    """Conversation数据传输对象。"""
    id: str
    conversation_type: str
    status: str
    members: List[ActorInfo]
    message_count: int
    title: Optional[str]
    last_message_at: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(cls, conversation: Conversation) -> "ConversationDTO":
        """从Conversation实体创建DTO。

        Args:
            conversation: Conversation实体

        Returns:
            ConversationDTO实例
        """
        return cls(
            id=str(conversation.id.value),
            conversation_type=conversation.conversation_type.value,
            status=conversation.status.value,
            members=[
                ActorInfo(
                    actor_type=member.actor_type.value,
                    actor_id=str(member.actor_id),
                )
                for member in conversation.members
            ],
            message_count=conversation.message_count,
            title=conversation.title,
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
        )
