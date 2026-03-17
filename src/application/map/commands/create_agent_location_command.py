"""创建Agent位置命令。"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.domain.map.entities.agent_location import AgentLocation
from src.domain.map.repositories.agent_location_repository import AgentLocationRepository
from src.domain.agent.repositories.agent_repository import AgentRepository
from src.application.map.dtos.agent_location_dto import AgentLocationDTO


@dataclass
class CreateAgentLocationCommand:
    """创建Agent位置命令。"""
    agent_id: UUID
    latitude: float
    longitude: float
    address: str
    is_active: bool = True
    display_order: int = 0
    metadata: Optional[dict] = None


class CreateAgentLocationCommandHandler:
    """创建Agent位置命令处理器。"""

    def __init__(
        self,
        location_repo: AgentLocationRepository,
        agent_repo: AgentRepository
    ):
        self.location_repo = location_repo
        self.agent_repo = agent_repo

    async def handle(self, command: CreateAgentLocationCommand) -> AgentLocationDTO:
        """处理创建Agent位置命令。

        Args:
            command: 创建命令

        Returns:
            AgentLocationDTO

        Raises:
            ValueError: Agent不存在或经纬度不合法
        """
        # 验证Agent是否存在
        agent = await self.agent_repo.find_by_id(command.agent_id)
        if not agent:
            raise ValueError(f"Agent with ID {command.agent_id} not found")

        # 创建Agent位置
        location = AgentLocation.create(
            agent_id=command.agent_id,
            latitude=command.latitude,
            longitude=command.longitude,
            address=command.address,
            is_active=command.is_active,
            display_order=command.display_order,
            metadata=command.metadata
        )

        # 保存
        location = await self.location_repo.save(location)

        # 返回DTO
        return AgentLocationDTO.from_entity(location, agent)
