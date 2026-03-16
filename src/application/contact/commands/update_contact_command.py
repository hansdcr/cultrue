"""Update contact command."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.application.contact.dtos.contact_dto import ContactDTO
from src.domain.contact.repositories.contact_repository import ContactRepository
from src.domain.shared.exceptions import NotFoundException


@dataclass
class UpdateContactCommand:
    """更新联系人命令。"""
    contact_id: UUID
    alias: Optional[str] = None
    is_favorite: Optional[bool] = None


class UpdateContactCommandHandler:
    """更新联系人命令处理器。"""

    def __init__(self, contact_repository: ContactRepository):
        self.contact_repository = contact_repository

    async def handle(self, command: UpdateContactCommand) -> ContactDTO:
        """处理更新联系人命令。

        Args:
            command: 更新命令

        Returns:
            ContactDTO

        Raises:
            NotFoundException: 如果Contact不存在
        """
        # 查找Contact
        contact = await self.contact_repository.find_by_id(command.contact_id)
        if not contact:
            raise NotFoundException(f"Contact with ID '{command.contact_id}' not found")

        # 更新别名
        if command.alias is not None:
            contact.update_alias(command.alias)

        # 更新收藏状态
        if command.is_favorite is not None:
            if command.is_favorite:
                contact.mark_as_favorite()
            else:
                contact.unmark_as_favorite()

        # 保存更新
        updated_contact = await self.contact_repository.update(contact)

        return ContactDTO.from_entity(updated_contact)
