"""Create agent command."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.application.agent.dtos.agent_dto import AgentDTO
from src.domain.agent.entities.agent import Agent
from src.domain.agent.repositories.agent_repository import AgentRepository
from src.domain.agent.value_objects.agent_id import AgentId
from src.domain.agent.value_objects.api_key import ApiKey
from src.domain.agent.value_objects.agent_config import AgentConfig
from src.domain.shared.exceptions import DomainException


@dataclass
class CreateAgentCommand:
    """创建Agent命令（管理员使用）。"""
    agent_id: str
    name: str
    avatar: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_config: Optional[dict] = None
    created_by: Optional[UUID] = None


class CreateAgentCommandHandler:
    """创建Agent命令处理器。"""

    def __init__(self, agent_repository: AgentRepository):
        self.agent_repository = agent_repository

    async def handle(self, command: CreateAgentCommand) -> AgentDTO:
        """处理创建Agent命令。

        Args:
            command: 创建命令

        Returns:
            AgentDTO

        Raises:
            DomainException: 如果agent_id已存在
        """
        # 检查agent_id是否已存在
        agent_id_vo = AgentId(command.agent_id)
        existing = await self.agent_repository.find_by_agent_id(agent_id_vo)
        if existing:
            raise DomainException(f"Agent ID '{command.agent_id}' already exists")

        # 生成API Key
        api_key = ApiKey.generate()

        # 解析模型配置
        model_config = None
        if command.model_config:
            model_config = AgentConfig.from_dict(command.model_config)

        # 创建Agent
        agent = Agent.create(
            agent_id=agent_id_vo,
            name=command.name,
            api_key=api_key,
            avatar=command.avatar,
            description=command.description,
            system_prompt=command.system_prompt,
            model_config=model_config,
            created_by=command.created_by,
        )

        # 保存Agent
        saved_agent = await self.agent_repository.save(agent)

        return AgentDTO.from_entity(saved_agent)
