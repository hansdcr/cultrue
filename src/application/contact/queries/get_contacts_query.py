"""Get contacts query."""
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from src.application.contact.dtos.contact_dto import ContactDTO
from src.domain.contact.enums.contact_type import ContactType
from src.domain.contact.repositories.contact_repository import ContactRepository
from src.domain.shared.value_objects.actor import Actor


@dataclass
class GetContactsQuery:
    """获取联系人列表查询。"""
    owner_type: str      # 'user' or 'agent'
    owner_id: UUID
    contact_type: Optional[str] = None
    limit: int = 20
    offset: int = 0


@dataclass
class GetContactsResult:
    """联系人列表结果。"""
    items: List[ContactDTO]
    total: int
    limit: int
    offset: int


class GetContactsQueryHandler:
    """获取联系人列表查询处理器。"""

    def __init__(self, contact_repository: ContactRepository):
        self.contact_repository = contact_repository

    async def handle(self, query: GetContactsQuery) -> GetContactsResult:
        """处理获取联系人列表查询。

        Args:
            query: 查询

        Returns:
            GetContactsResult
        """
        # 创建owner Actor
        owner = self._create_actor(query.owner_type, query.owner_id)

        # 解析联系人类型
        contact_type_enum = None
        if query.contact_type:
            contact_type_enum = ContactType(query.contact_type)

        # 查询联系人列表
        contacts = await self.contact_repository.find_by_owner(
            owner=owner,
            contact_type=contact_type_enum,
            limit=query.limit,
            offset=query.offset,
        )

        # 统计总数
        total = await self.contact_repository.count_by_owner(
            owner=owner,
            contact_type=contact_type_enum,
        )

        # 转换为DTO
        items = [ContactDTO.from_entity(contact) for contact in contacts]

        return GetContactsResult(
            items=items,
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

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
