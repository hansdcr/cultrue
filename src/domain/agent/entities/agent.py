"""Agent entity."""
import bcrypt
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from src.domain.agent.value_objects.agent_id import AgentId
from src.domain.agent.value_objects.api_key import ApiKey
from src.domain.agent.value_objects.agent_config import AgentConfig
from src.domain.shared.value_objects.actor import Actor


@dataclass
class Agent:
    """Agent实体。

    Agent是系统中的AI助手，可以独立认证和参与对话。
    """
    id: UUID
    agent_id: AgentId
    name: str
    avatar: Optional[str]
    description: Optional[str]
    system_prompt: Optional[str]
    model_config: AgentConfig
    api_key_prefix: str
    api_key_hash: str
    is_active: bool
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        agent_id: AgentId,
        name: str,
        api_key: ApiKey,
        avatar: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model_config: Optional[AgentConfig] = None,
        created_by: Optional[UUID] = None,
    ) -> "Agent":
        """创建Agent实体。

        Args:
            agent_id: Agent ID
            name: Agent名称
            api_key: API Key
            avatar: 头像URL
            description: 描述
            system_prompt: 系统提示词
            model_config: 模型配置
            created_by: 创建者的user_id

        Returns:
            Agent实例
        """
        now = datetime.utcnow()
        api_key_hash = bcrypt.hashpw(
            api_key.value.encode(),
            bcrypt.gensalt()
        ).decode()

        return cls(
            id=uuid4(),
            agent_id=agent_id,
            name=name,
            avatar=avatar,
            description=description,
            system_prompt=system_prompt,
            model_config=model_config or AgentConfig(),
            api_key_prefix=api_key.get_prefix(),
            api_key_hash=api_key_hash,
            is_active=True,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

    def to_actor(self) -> Actor:
        """转换为Actor。

        Returns:
            Actor值对象
        """
        return Actor.from_agent(self.id)

    def verify_api_key(self, api_key: ApiKey) -> bool:
        """验证API Key。

        Args:
            api_key: 要验证的API Key

        Returns:
            验证成功返回True，否则返回False
        """
        return bcrypt.checkpw(
            api_key.value.encode(),
            self.api_key_hash.encode()
        )

    def regenerate_api_key(self) -> ApiKey:
        """重新生成API Key。

        Returns:
            新生成的API Key（仅此一次返回明文）
        """
        new_api_key = ApiKey.generate()
        self.api_key_prefix = new_api_key.get_prefix()
        self.api_key_hash = bcrypt.hashpw(
            new_api_key.value.encode(),
            bcrypt.gensalt()
        ).decode()
        self.updated_at = datetime.utcnow()
        return new_api_key

    def update_info(
        self,
        name: Optional[str] = None,
        avatar: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model_config: Optional[AgentConfig] = None,
    ) -> None:
        """更新Agent信息。

        Args:
            name: 新名称
            avatar: 新头像URL
            description: 新描述
            system_prompt: 新系统提示词
            model_config: 新模型配置
        """
        if name is not None:
            self.name = name
        if avatar is not None:
            self.avatar = avatar
        if description is not None:
            self.description = description
        if system_prompt is not None:
            self.system_prompt = system_prompt
        if model_config is not None:
            self.model_config = model_config
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """停用Agent。"""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """激活Agent。"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
