"""Agent地理位置DTO。"""
from dataclasses import dataclass
from typing import Optional

from src.domain.map.entities.agent_location import AgentLocation
from src.domain.agent.entities.agent import Agent


@dataclass
class AgentInfoDTO:
    """Agent信息DTO（嵌套在AgentLocationDTO中）。"""
    id: str
    agent_id: str
    name: str
    avatar: Optional[str]
    description: Optional[str]


@dataclass
class AgentLocationDTO:
    """Agent位置DTO。"""
    location_id: str
    agent: AgentInfoDTO
    latitude: float
    longitude: float
    address: str
    is_active: bool
    display_order: int
    distance: Optional[float] = None  # 距离（米），仅在nearby查询时返回
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(
        cls,
        location: AgentLocation,
        agent: Agent,
        distance: Optional[float] = None
    ) -> "AgentLocationDTO":
        """从实体创建DTO。

        Args:
            location: Agent位置实体
            agent: Agent实体
            distance: 距离（米）

        Returns:
            AgentLocationDTO实例
        """
        return cls(
            location_id=str(location.id),
            agent=AgentInfoDTO(
                id=str(agent.id),
                agent_id=agent.agent_id.value,
                name=agent.name,
                avatar=agent.avatar,
                description=agent.description
            ),
            latitude=location.latitude,
            longitude=location.longitude,
            address=location.address,
            is_active=location.is_active,
            display_order=location.display_order,
            distance=distance,
            created_at=location.created_at.isoformat(),
            updated_at=location.updated_at.isoformat()
        )
