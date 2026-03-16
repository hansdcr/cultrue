"""Update agent command."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.application.agent.dtos.agent_dto import AgentDTO
from src.domain.agent.repositories.agent_repository import AgentRepository
from src.domain.agent.value_objects.agent_config import AgentConfig
from src.domain.shared.exceptions import NotFoundException


@dataclass
class UpdateAgentCommand:
    """更新Agent命令。"""
    agent_id: UUID
    name: Optional[str] = None
    avatar: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_config: Optional[dict] = None


class UpdateAgentCommandHandler:
    """更新Agent命令处理器。"""

    def __init__(self, agent_repository: AgentRepository):
        self.agent_repository = agent_repository

    async def handle(self, command: UpdateAgentCommand) -> AgentDTO:
        """处理更新Agent命令。

        Args:
            command: 更新命令

        Returns:
            AgentDTO

        Raises:
            NotFoundException: 如果Agent不存在
        """
        # 查找Agent
        agent = await self.agent_repository.find_by_id(command.agent_id)
        if not agent:
            raise NotFoundException(f"Agent with ID '{command.agent_id}' not found")

        # 解析模型配置
        model_config = None
        if command.model_config:
            model_config = AgentConfig.from_dict(command.model_config)

        # 更新Agent信息
        agent.update_info(
            name=command.name,
            avatar=command.avatar,
            description=command.description,
            system_prompt=command.system_prompt,
            model_config=model_config,
        )

        # 保存更新
        updated_agent = await self.agent_repository.update(agent)

        return AgentDTO.from_entity(updated_agent)
