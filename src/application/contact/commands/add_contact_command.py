"""Add contact command."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.application.contact.dtos.contact_dto import ContactDTO
from src.domain.contact.entities.contact import Contact
from src.domain.contact.enums.contact_type import ContactType
from src.domain.contact.repositories.contact_repository import ContactRepository
from src.domain.shared.value_objects.actor import Actor
from src.domain.shared.enums.actor_type import ActorType
from src.domain.shared.exceptions import DomainException


@dataclass
class AddContactCommand:
    """添加联系人命令。"""
    owner_type: str      # 'user' or 'agent'
    owner_id: UUID
    target_type: str     # 'user' or 'agent'
    target_id: UUID
    contact_type: str = "friend"
    alias: Optional[str] = None


class AddContactCommandHandler:
    """添加联系人命令处理器。"""

    def __init__(self, contact_repository: ContactRepository):
        self.contact_repository = contact_repository

    async def handle(self, command: AddContactCommand) -> ContactDTO:
        """处理添加联系人命令。

        Args:
            command: 添加命令

        Returns:
            ContactDTO

        Raises:
            DomainException: 如果联系人关系已存在
        """
        # 创建Actor
        owner = self._create_actor(command.owner_type, command.owner_id)
        target = self._create_actor(command.target_type, command.target_id)

        # 检查是否已存在
        existing = await self.contact_repository.find_by_owner_and_target(owner, target)
        if existing:
            raise DomainException("Contact relationship already exists")

        # 解析联系人类型
        contact_type = ContactType(command.contact_type)

        # 创建Contact
        contact = Contact.create(
            owner=owner,
            target=target,
            contact_type=contact_type,
            alias=command.alias,
        )

        # 保存Contact（仓储层会自动处理Participant）
        saved_contact = await self.contact_repository.save(contact)

        return ContactDTO.from_entity(saved_contact)

    def _create_actor(self, actor_type: str, actor_id: UUID) -> Actor:
        """创建Actor。

        Args:
            actor_type: Actor类型
            actor_id: Actor ID

        Returns:
            Actor实例
        """
        if actor_type == "user":
            return Actor.from_user(actor_id)
        elif actor_type == "agent":
            return Actor.from_agent(actor_id)
        else:
            raise ValueError(f"Invalid actor_type: {actor_type}")
