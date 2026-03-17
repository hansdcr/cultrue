"""查询某个Agent的所有位置。"""
from dataclasses import dataclass
from typing import List
from uuid import UUID

from src.domain.map.repositories.agent_location_repository import AgentLocationRepository
from src.domain.agent.repositories.agent_repository import AgentRepository
from src.application.map.dtos.agent_location_dto import AgentLocationDTO


@dataclass
class GetAgentLocationsQuery:
    """查询某个Agent的所有位置。"""
    agent_id: UUID
    only_active: bool = True


@dataclass
class GetAgentLocationsResult:
    """查询Agent位置结果。"""
    items: List[AgentLocationDTO]
    total: int


class GetAgentLocationsQueryHandler:
    """查询Agent位置处理器。"""

    def __init__(
        self,
        location_repo: AgentLocationRepository,
        agent_repo: AgentRepository
    ):
        self.location_repo = location_repo
        self.agent_repo = agent_repo

    async def handle(self, query: GetAgentLocationsQuery) -> GetAgentLocationsResult:
        """处理查询Agent位置。

        Args:
            query: 查询参数

        Returns:
            GetAgentLocationsResult

        Raises:
            ValueError: Agent不存在
        """
        # 验证Agent是否存在
        agent = await self.agent_repo.find_by_id(query.agent_id)
        if not agent:
            raise ValueError(f"Agent with ID {query.agent_id} not found")

        # 查询Agent的所有位置
        locations = await self.location_repo.find_by_agent_id(query.agent_id)

        # 过滤激活状态
        if query.only_active:
            locations = [loc for loc in locations if loc.is_active]

        # 转换为DTO
        items = [
            AgentLocationDTO.from_entity(location, agent)
            for location in locations
        ]

        return GetAgentLocationsResult(
            items=items,
            total=len(items)
        )
