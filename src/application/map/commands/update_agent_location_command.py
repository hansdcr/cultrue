"""更新Agent位置命令。"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.application.map.dtos.agent_location_dto import AgentLocationDTO
from src.domain.map.repositories.agent_location_repository import (
    AgentLocationRepository,
)
from src.domain.agent.repositories.agent_repository import AgentRepository


@dataclass
class UpdateAgentLocationCommand:
    """更新Agent位置命令。"""

    location_id: UUID
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    metadata: Optional[dict] = None


class UpdateAgentLocationCommandHandler:
    """更新Agent位置命令处理器。"""

    def __init__(
        self,
        location_repo: AgentLocationRepository,
        agent_repo: AgentRepository,
    ):
        self.location_repo = location_repo
        self.agent_repo = agent_repo

    async def handle(
        self, command: UpdateAgentLocationCommand
    ) -> AgentLocationDTO:
        """处理命令。"""
        # 查找位置
        location = await self.location_repo.find_by_id(command.location_id)
        if not location:
            raise ValueError(f"Location not found: {command.location_id}")

        # 更新位置信息
        if (
            command.latitude is not None
            and command.longitude is not None
            and command.address is not None
        ):
            location.update_location(
                command.latitude, command.longitude, command.address
            )

        # 更新激活状态
        if command.is_active is not None:
            if command.is_active:
                location.activate()
            else:
                location.deactivate()

        # 更新显示顺序
        if command.display_order is not None:
            location.display_order = command.display_order

        # 更新元数据
        if command.metadata is not None:
            location.metadata = command.metadata

        # 保存更新
        updated_location = await self.location_repo.update(location)

        # 查找Agent
        agent = await self.agent_repo.find_by_id(updated_location.agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {updated_location.agent_id}")

        # 转换为DTO
        return await AgentLocationDTO.from_entity(updated_location, agent)
