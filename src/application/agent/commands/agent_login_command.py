"""Agent登录命令。

处理Agent通过API Key登录的业务逻辑，返回JWT Token。
"""
from dataclasses import dataclass

from src.domain.agent.repositories.agent_repository import AgentRepository
from src.domain.agent.value_objects.agent_id import AgentId
from src.domain.agent.value_objects.api_key import ApiKey
from src.infrastructure.security.jwt_service import jwt_service
from ..dtos.agent_dto import AgentDTO


@dataclass
class AgentLoginCommand:
    """Agent登录命令。"""
    agent_id: str
    api_key: str


@dataclass
class AgentLoginResult:
    """Agent登录结果。"""
    agent: AgentDTO
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AgentLoginCommandHandler:
    """Agent登录命令处理器。"""

    def __init__(self, agent_repository: AgentRepository) -> None:
        self._agent_repository = agent_repository

    async def handle(self, command: AgentLoginCommand) -> AgentLoginResult:
        """处理Agent登录命令。

        Args:
            command: 登录命令（agent_id + api_key）

        Returns:
            AgentLoginResult（包含Agent信息和JWT Token）

        Raises:
            ValueError: 如果agent_id不存在、API Key错误或Agent未激活
        """
        # 查找Agent
        agent_id_vo = AgentId(command.agent_id)
        agent = await self._agent_repository.find_by_agent_id(agent_id_vo)
        if not agent:
            raise ValueError("Invalid agent_id or api_key")

        # 验证API Key
        try:
            api_key_vo = ApiKey(command.api_key)
        except ValueError:
            raise ValueError("Invalid agent_id or api_key")

        if not agent.verify_api_key(api_key_vo):
            raise ValueError("Invalid agent_id or api_key")

        # 检查Agent是否激活
        if not agent.is_active:
            raise ValueError("Agent is not active")

        # 生成JWT Token（sub 使用 agent_id 字符串，加前缀区分）
        subject = f"agent:{agent.agent_id.value}"
        access_token = jwt_service.create_access_token(subject)
        refresh_token = jwt_service.create_refresh_token(subject)

        return AgentLoginResult(
            agent=AgentDTO.from_entity(agent),
            access_token=access_token,
            refresh_token=refresh_token,
        )
