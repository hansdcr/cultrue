"""Contact repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.contact.entities.contact import Contact
from src.domain.contact.enums.contact_type import ContactType
from src.domain.shared.value_objects.actor import Actor


class ContactRepository(ABC):
    """Contact仓储接口。"""

    @abstractmethod
    async def save(self, contact: Contact) -> Contact:
        """保存Contact。

        Args:
            contact: Contact实例

        Returns:
            保存后的Contact实例
        """
        pass

    @abstractmethod
    async def find_by_id(self, contact_id: UUID) -> Optional[Contact]:
        """根据ID查找Contact。

        Args:
            contact_id: Contact的UUID

        Returns:
            Contact实例，如果不存在返回None
        """
        pass

    @abstractmethod
    async def find_by_owner_and_target(
        self,
        owner: Actor,
        target: Actor
    ) -> Optional[Contact]:
        """根据owner和target查找Contact。

        Args:
            owner: 拥有者
            target: 目标

        Returns:
            Contact实例，如果不存在返回None
        """
        pass

    @abstractmethod
    async def find_by_owner(
        self,
        owner: Actor,
        contact_type: Optional[ContactType] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Contact]:
        """查找owner的所有联系人。

        Args:
            owner: 拥有者
            contact_type: 联系人类型（None表示不过滤）
            limit: 限制数量
            offset: 偏移量

        Returns:
            Contact列表
        """
        pass

    @abstractmethod
    async def update(self, contact: Contact) -> Contact:
        """更新Contact。

        Args:
            contact: Contact实例

        Returns:
            更新后的Contact实例
        """
        pass

    @abstractmethod
    async def delete(self, contact_id: UUID) -> None:
        """删除Contact。

        Args:
            contact_id: Contact的UUID
        """
        pass

    @abstractmethod
    async def count_by_owner(
        self,
        owner: Actor,
        contact_type: Optional[ContactType] = None
    ) -> int:
        """统计owner的联系人数量。

        Args:
            owner: 拥有者
            contact_type: 联系人类型（None表示不过滤）

        Returns:
            联系人数量
        """
        pass
