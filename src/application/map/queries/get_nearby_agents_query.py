"""查询周边Agent。"""
from dataclasses import dataclass
from typing import List

from src.domain.map.repositories.agent_location_repository import AgentLocationRepository
from src.application.map.dtos.agent_location_dto import AgentLocationDTO


@dataclass
class GetNearbyAgentsQuery:
    """查询周边Agent。"""
    latitude: float
    longitude: float
    radius: int = 5000  # 默认5公里
    limit: int = 10
    only_active: bool = True


@dataclass
class GetNearbyAgentsResult:
    """查询周边Agent结果。"""
    items: List[AgentLocationDTO]
    total: int
    center: dict  # {"latitude": float, "longitude": float}
    radius: int


class GetNearbyAgentsQueryHandler:
    """查询周边Agent处理器。"""

    def __init__(self, location_repo: AgentLocationRepository):
        self.location_repo = location_repo

    async def handle(self, query: GetNearbyAgentsQuery) -> GetNearbyAgentsResult:
        """处理查询周边Agent。

        Args:
            query: 查询参数

        Returns:
            GetNearbyAgentsResult
        """
        # 查询周边位置（包含Agent信息和距离）
        results = await self.location_repo.find_nearby_with_agents(
            latitude=query.latitude,
            longitude=query.longitude,
            radius=query.radius,
            limit=query.limit,
            only_active=query.only_active
        )

        # 转换为DTO
        items = [
            AgentLocationDTO.from_entity(location, agent, distance)
            for location, agent, distance in results
        ]

        return GetNearbyAgentsResult(
            items=items,
            total=len(items),
            center={
                "latitude": query.latitude,
                "longitude": query.longitude
            },
            radius=query.radius
        )
