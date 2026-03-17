"""Conversation entity."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from src.domain.messaging.enums.conversation_type import ConversationType
from src.domain.messaging.enums.conversation_status import ConversationStatus
from src.domain.messaging.value_objects.conversation_id import ConversationId
from src.domain.shared.value_objects.actor import Actor


@dataclass
class Conversation:
    """会话实体。

    支持User↔User、User↔Agent、Agent↔Agent以及群聊。
    """
    id: ConversationId
    conversation_type: ConversationType
    status: ConversationStatus
    members: List[Actor]
    message_count: int
    title: Optional[str] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_member(self, actor: Actor) -> None:
        """添加成员。

        Args:
            actor: 要添加的Actor
        """
        if actor not in self.members:
            self.members.append(actor)
            self.updated_at = datetime.now(timezone.utc)

    def remove_member(self, actor: Actor) -> None:
        """移除成员。

        Args:
            actor: 要移除的Actor
        """
        if actor in self.members:
            self.members.remove(actor)
            self.updated_at = datetime.now(timezone.utc)

    def has_member(self, actor: Actor) -> bool:
        """检查是否包含指定成员。

        Args:
            actor: 要检查的Actor

        Returns:
            如果包含该成员返回True，否则返回False
        """
        return actor in self.members

    def is_direct(self) -> bool:
        """判断是否为一对一会话。

        Returns:
            如果是一对一会话返回True，否则返回False
        """
        return self.conversation_type == ConversationType.DIRECT

    def is_group(self) -> bool:
        """判断是否为群聊。

        Returns:
            如果是群聊返回True，否则返回False
        """
        return self.conversation_type == ConversationType.GROUP

    @classmethod
    def create_direct(cls, actor1: Actor, actor2: Actor) -> "Conversation":
        """创建一对一会话。

        Args:
            actor1: 第一个参与者
            actor2: 第二个参与者

        Returns:
            Conversation实例
        """
        return cls(
            id=ConversationId.generate(),
            conversation_type=ConversationType.DIRECT,
            status=ConversationStatus.ACTIVE,
            members=[actor1, actor2],
            message_count=0,
            title=None,
            last_message_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    @classmethod
    def create_group(cls, title: str, members: List[Actor]) -> "Conversation":
        """创建群聊。

        Args:
            title: 群聊标题
            members: 成员列表

        Returns:
            Conversation实例
        """
        return cls(
            id=ConversationId.generate(),
            conversation_type=ConversationType.GROUP,
            status=ConversationStatus.ACTIVE,
            members=members,
            message_count=0,
            title=title,
            last_message_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
