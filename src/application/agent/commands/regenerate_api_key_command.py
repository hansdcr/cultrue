"""Regenerate API key command."""
from dataclasses import dataclass
from uuid import UUID

from src.domain.agent.repositories.agent_repository import AgentRepository
from src.domain.shared.exceptions import NotFoundException


@dataclass
class RegenerateApiKeyCommand:
    """重新生成API Key命令。"""
    agent_id: UUID


@dataclass
class RegenerateApiKeyResult:
    """重新生成API Key结果。"""
    api_key: str  # 明文API Key，仅此一次返回


class RegenerateApiKeyCommandHandler:
    """重新生成API Key命令处理器。"""

    def __init__(self, agent_repository: AgentRepository):
        self.agent_repository = agent_repository

    async def handle(self, command: RegenerateApiKeyCommand) -> RegenerateApiKeyResult:
        """处理重新生成API Key命令。

        Args:
            command: 命令

        Returns:
            RegenerateApiKeyResult包含新的API Key

        Raises:
            NotFoundException: 如果Agent不存在
        """
        # 查找Agent
        agent = await self.agent_repository.find_by_id(command.agent_id)
        if not agent:
            raise NotFoundException(f"Agent with ID '{command.agent_id}' not found")

        # 重新生成API Key
        new_api_key = agent.regenerate_api_key()

        # 更新Agent
        await self.agent_repository.update(agent)

        # 返回新的API Key（明文，仅此一次）
        return RegenerateApiKeyResult(api_key=new_api_key.value)
