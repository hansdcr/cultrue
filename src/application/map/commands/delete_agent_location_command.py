"""删除Agent位置命令。"""
from dataclasses import dataclass
from uuid import UUID

from src.domain.map.repositories.agent_location_repository import (
    AgentLocationRepository,
)


@dataclass
class DeleteAgentLocationCommand:
    """删除Agent位置命令。"""

    location_id: UUID


class DeleteAgentLocationCommandHandler:
    """删除Agent位置命令处理器。"""

    def __init__(self, location_repo: AgentLocationRepository):
        self.location_repo = location_repo

    async def handle(self, command: DeleteAgentLocationCommand) -> None:
        """处理命令。"""
        # 查找位置
        location = await self.location_repo.find_by_id(command.location_id)
        if not location:
            raise ValueError(f"Location not found: {command.location_id}")

        # 删除位置
        await self.location_repo.delete(command.location_id)
