"""Get agent query."""
from dataclasses import dataclass
from uuid import UUID

from src.application.agent.dtos.agent_dto import AgentDTO
from src.domain.agent.repositories.agent_repository import AgentRepository
from src.domain.shared.exceptions import NotFoundException


@dataclass
class GetAgentQuery:
    """获取Agent查询。"""
    agent_id: UUID


class GetAgentQueryHandler:
    """获取Agent查询处理器。"""

    def __init__(self, agent_repository: AgentRepository):
        self.agent_repository = agent_repository

    async def handle(self, query: GetAgentQuery) -> AgentDTO:
        """处理获取Agent查询。

        Args:
            query: 查询

        Returns:
            AgentDTO

        Raises:
            NotFoundException: 如果Agent不存在
        """
        agent = await self.agent_repository.find_by_id(query.agent_id)
        if not agent:
            raise NotFoundException(f"Agent with ID '{query.agent_id}' not found")

        return AgentDTO.from_entity(agent)
