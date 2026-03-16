"""Contact entity."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from src.domain.contact.enums.contact_type import ContactType
from src.domain.shared.value_objects.actor import Actor


@dataclass
class Contact:
    """联系人实体。

    支持User-User、User-Agent、Agent-Agent关系。
    """
    id: UUID
    owner: Actor
    target: Actor
    contact_type: ContactType
    alias: Optional[str]
    is_favorite: bool
    last_interaction_at: Optional[datetime]
    created_at: datetime

    @classmethod
    def create(
        cls,
        owner: Actor,
        target: Actor,
        contact_type: ContactType = ContactType.FRIEND,
        alias: Optional[str] = None
    ) -> "Contact":
        """创建联系人关系。

        Args:
            owner: 拥有者（可以是User或Agent）
            target: 目标（可以是User或Agent）
            contact_type: 联系人类型
            alias: 备注名

        Returns:
            Contact实例
        """
        return cls(
            id=uuid4(),
            owner=owner,
            target=target,
            contact_type=contact_type,
            alias=alias,
            is_favorite=contact_type == ContactType.FAVORITE,
            last_interaction_at=None,
            created_at=datetime.utcnow(),
        )

    def update_alias(self, alias: str) -> None:
        """更新备注名。

        Args:
            alias: 新的备注名
        """
        self.alias = alias

    def mark_as_favorite(self) -> None:
        """标记为收藏。"""
        self.is_favorite = True
        self.contact_type = ContactType.FAVORITE

    def unmark_as_favorite(self) -> None:
        """取消收藏标记。"""
        self.is_favorite = False
        if self.contact_type == ContactType.FAVORITE:
            self.contact_type = ContactType.FRIEND

    def record_interaction(self) -> None:
        """记录交互时间。"""
        self.last_interaction_at = datetime.utcnow()

    def block(self) -> None:
        """屏蔽联系人。"""
        self.contact_type = ContactType.BLOCKED

    def unblock(self) -> None:
        """取消屏蔽。"""
        if self.contact_type == ContactType.BLOCKED:
            self.contact_type = ContactType.FRIEND
