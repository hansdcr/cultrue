"""List agents query."""
from dataclasses import dataclass
from typing import List, Optional

from src.application.agent.dtos.agent_dto import AgentDTO
from src.domain.agent.repositories.agent_repository import AgentRepository


@dataclass
class ListAgentsQuery:
    """获取Agent列表查询。"""
    is_active: Optional[bool] = None
    limit: int = 20
    offset: int = 0


@dataclass
class ListAgentsResult:
    """Agent列表结果。"""
    items: List[AgentDTO]
    total: int
    limit: int
    offset: int


class ListAgentsQueryHandler:
    """获取Agent列表查询处理器。"""

    def __init__(self, agent_repository: AgentRepository):
        self.agent_repository = agent_repository

    async def handle(self, query: ListAgentsQuery) -> ListAgentsResult:
        """处理获取Agent列表查询。

        Args:
            query: 查询

        Returns:
            ListAgentsResult
        """
        # 查询Agent列表
        agents = await self.agent_repository.find_all(
            is_active=query.is_active,
            limit=query.limit,
            offset=query.offset,
        )

        # 统计总数
        total = await self.agent_repository.count(is_active=query.is_active)

        # 转换为DTO
        items = [AgentDTO.from_entity(agent) for agent in agents]

        return ListAgentsResult(
            items=items,
            total=total,
            limit=query.limit,
            offset=query.offset,
        )
