"""Remove contact command."""
from dataclasses import dataclass
from uuid import UUID

from src.domain.contact.repositories.contact_repository import ContactRepository
from src.domain.shared.exceptions import NotFoundException


@dataclass
class RemoveContactCommand:
    """删除联系人命令。"""
    contact_id: UUID


class RemoveContactCommandHandler:
    """删除联系人命令处理器。"""

    def __init__(self, contact_repository: ContactRepository):
        self.contact_repository = contact_repository

    async def handle(self, command: RemoveContactCommand) -> None:
        """处理删除联系人命令。

        Args:
            command: 删除命令

        Raises:
            NotFoundException: 如果Contact不存在
        """
        # 检查Contact是否存在
        contact = await self.contact_repository.find_by_id(command.contact_id)
        if not contact:
            raise NotFoundException(f"Contact with ID '{command.contact_id}' not found")

        # 删除Contact
        await self.contact_repository.delete(command.contact_id)
