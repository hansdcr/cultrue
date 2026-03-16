"""Agent DTOs."""
from dataclasses import dataclass
from typing import Optional

from src.domain.agent.entities.agent import Agent
from src.domain.agent.value_objects.api_key import ApiKey


@dataclass
class AgentDTO:
    """Agent数据传输对象。"""
    id: str
    agent_id: str
    name: str
    avatar: Optional[str]
    description: Optional[str]
    system_prompt: Optional[str]
    model_config: dict
    api_key_prefix: str
    is_active: bool
    created_by: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(cls, agent: Agent) -> "AgentDTO":
        """从Agent实体创建DTO。

        Args:
            agent: Agent实体

        Returns:
            AgentDTO实例
        """
        return cls(
            id=str(agent.id),
            agent_id=agent.agent_id.value,
            name=agent.name,
            avatar=agent.avatar,
            description=agent.description,
            system_prompt=agent.system_prompt,
            model_config=agent.model_config.to_dict(),
            api_key_prefix=agent.api_key_prefix,
            is_active=agent.is_active,
            created_by=str(agent.created_by) if agent.created_by else None,
            created_at=agent.created_at.isoformat(),
            updated_at=agent.updated_at.isoformat(),
        )


@dataclass
class RegisterAgentResult:
    """Agent注册结果。

    包含Agent信息和API Key（仅在注册时返回一次）。
    """
    agent: AgentDTO
    api_key: str  # 明文API Key，仅此一次返回

    @classmethod
    def create(cls, agent: Agent, api_key: ApiKey) -> "RegisterAgentResult":
        """创建注册结果。

        Args:
            agent: Agent实体
            api_key: API Key

        Returns:
            RegisterAgentResult实例
        """
        return cls(
            agent=AgentDTO.from_entity(agent),
            api_key=api_key.value,
        )
