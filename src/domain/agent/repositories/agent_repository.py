"""Agent repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.agent.entities.agent import Agent
from src.domain.agent.value_objects.agent_id import AgentId


class AgentRepository(ABC):
    """Agent仓储接口。"""

    @abstractmethod
    async def save(self, agent: Agent) -> Agent:
        """保存Agent。

        Args:
            agent: Agent实例

        Returns:
            保存后的Agent实例
        """
        pass

    @abstractmethod
    async def find_by_id(self, agent_id: UUID) -> Optional[Agent]:
        """根据ID查找Agent。

        Args:
            agent_id: Agent的UUID

        Returns:
            Agent实例，如果不存在返回None
        """
        pass

    @abstractmethod
    async def find_by_agent_id(self, agent_id: AgentId) -> Optional[Agent]:
        """根据agent_id查找Agent。

        Args:
            agent_id: Agent ID值对象

        Returns:
            Agent实例，如果不存在返回None
        """
        pass

    @abstractmethod
    async def find_by_api_key_prefix(self, prefix: str) -> Optional[Agent]:
        """根据API Key前缀查找Agent。

        用于快速定位Agent，然后再验证完整的API Key。

        Args:
            prefix: API Key前缀

        Returns:
            Agent实例，如果不存在返回None
        """
        pass

    @abstractmethod
    async def find_all(
        self,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Agent]:
        """查找所有Agent。

        Args:
            is_active: 是否激活（None表示不过滤）
            limit: 限制数量
            offset: 偏移量

        Returns:
            Agent列表
        """
        pass

    @abstractmethod
    async def update(self, agent: Agent) -> Agent:
        """更新Agent。

        Args:
            agent: Agent实例

        Returns:
            更新后的Agent实例
        """
        pass

    @abstractmethod
    async def delete(self, agent_id: UUID) -> None:
        """删除Agent。

        Args:
            agent_id: Agent的UUID
        """
        pass

    @abstractmethod
    async def count(self, is_active: Optional[bool] = None, name: Optional[str] = None) -> int:
        """统计Agent数量。

        Args:
            is_active: 是否激活（None表示不过滤）

        Returns:
            Agent数量
        """
        pass
