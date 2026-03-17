"""获取Agent位置详情查询。"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.application.map.dtos.agent_location_dto import AgentLocationDTO
from src.domain.map.repositories.agent_location_repository import (
    AgentLocationRepository,
)
from src.domain.agent.repositories.agent_repository import AgentRepository


@dataclass
class GetAgentLocationQuery:
    """获取Agent位置详情查询。"""

    location_id: UUID


class GetAgentLocationQueryHandler:
    """获取Agent位置详情查询处理器。"""

    def __init__(
        self,
        location_repo: AgentLocationRepository,
        agent_repo: AgentRepository,
    ):
        self.location_repo = location_repo
        self.agent_repo = agent_repo

    async def handle(
        self, query: GetAgentLocationQuery
    ) -> Optional[AgentLocationDTO]:
        """处理查询。"""
        # 查找位置
        location = await self.location_repo.find_by_id(query.location_id)
        if not location:
            return None

        # 查找Agent
        agent = await self.agent_repo.find_by_id(location.agent_id)
        if not agent:
            return None

        # 转换为DTO
        return await AgentLocationDTO.from_entity(location, agent)
