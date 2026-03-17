"""Agent地理位置仓储接口。"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from src.domain.map.entities.agent_location import AgentLocation


class AgentLocationRepository(ABC):
    """Agent地理位置仓储接口。"""

    @abstractmethod
    async def save(self, location: AgentLocation) -> AgentLocation:
        """保存Agent位置。

        Args:
            location: Agent位置实体

        Returns:
            保存后的Agent位置实体
        """
        pass

    @abstractmethod
    async def find_by_id(self, location_id: UUID) -> Optional[AgentLocation]:
        """根据ID查找位置。

        Args:
            location_id: 位置ID

        Returns:
            Agent位置实体，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def find_by_agent_id(self, agent_id: UUID) -> List[AgentLocation]:
        """查找Agent的所有位置。

        Args:
            agent_id: Agent ID

        Returns:
            Agent位置列表
        """
        pass

    @abstractmethod
    async def find_nearby(
        self,
        latitude: float,
        longitude: float,
        radius: int,
        limit: int = 10,
        only_active: bool = True
    ) -> List[AgentLocation]:
        """查找周边位置。

        Args:
            latitude: 纬度
            longitude: 经度
            radius: 半径（米）
            limit: 返回数量限制
            only_active: 是否只返回激活的位置

        Returns:
            Agent位置列表
        """
        pass

    @abstractmethod
    async def update(self, location: AgentLocation) -> AgentLocation:
        """更新位置。

        Args:
            location: Agent位置实体

        Returns:
            更新后的Agent位置实体
        """
        pass

    @abstractmethod
    async def delete(self, location_id: UUID) -> None:
        """删除位置。

        Args:
            location_id: 位置ID
        """
        pass

    @abstractmethod
    async def count_by_agent_id(self, agent_id: UUID) -> int:
        """统计Agent的位置数量。

        Args:
            agent_id: Agent ID

        Returns:
            位置数量
        """
        pass
