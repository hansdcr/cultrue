"""Contact DTO."""
from dataclasses import dataclass
from typing import Optional

from src.domain.contact.entities.contact import Contact


@dataclass
class ActorInfo:
    """Actor信息。"""
    actor_type: str
    actor_id: str


@dataclass
class ContactDTO:
    """Contact数据传输对象。"""
    id: str
    owner: ActorInfo
    target: ActorInfo
    contact_type: str
    alias: Optional[str]
    is_favorite: bool
    last_interaction_at: Optional[str]
    created_at: str

    @classmethod
    def from_entity(cls, contact: Contact) -> "ContactDTO":
        """从Contact实体创建DTO。

        Args:
            contact: Contact实体

        Returns:
            ContactDTO实例
        """
        return cls(
            id=str(contact.id),
            owner=ActorInfo(
                actor_type=contact.owner.actor_type.value,
                actor_id=str(contact.owner.actor_id),
            ),
            target=ActorInfo(
                actor_type=contact.target.actor_type.value,
                actor_id=str(contact.target.actor_id),
            ),
            contact_type=contact.contact_type.value,
            alias=contact.alias,
            is_favorite=contact.is_favorite,
            last_interaction_at=contact.last_interaction_at.isoformat() if contact.last_interaction_at else None,
            created_at=contact.created_at.isoformat(),
        )
