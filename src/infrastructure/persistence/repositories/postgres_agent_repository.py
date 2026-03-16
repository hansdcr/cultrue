"""PostgreSQL Agent repository implementation."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.agent.entities.agent import Agent
from src.domain.agent.repositories.agent_repository import AgentRepository
from src.domain.agent.value_objects.agent_id import AgentId
from src.domain.agent.value_objects.agent_config import AgentConfig
from src.infrastructure.persistence.models.agent_model import AgentModel


class PostgresAgentRepository(AgentRepository):
    """PostgreSQL Agent仓储实现。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, agent: Agent) -> Agent:
        """保存Agent。"""
        model = self._to_model(agent)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def find_by_id(self, agent_id: UUID) -> Optional[Agent]:
        """根据ID查找Agent。"""
        stmt = select(AgentModel).where(AgentModel.id == agent_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_agent_id(self, agent_id: AgentId) -> Optional[Agent]:
        """根据agent_id查找Agent。"""
        stmt = select(AgentModel).where(AgentModel.agent_id == agent_id.value)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_api_key_prefix(self, prefix: str) -> Optional[Agent]:
        """根据API Key前缀查找Agent。"""
        stmt = select(AgentModel).where(AgentModel.api_key_prefix == prefix)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_all(
        self,
        is_active: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Agent]:
        """查找所有Agent。"""
        stmt = select(AgentModel)

        if is_active is not None:
            stmt = stmt.where(AgentModel.is_active == is_active)

        stmt = stmt.limit(limit).offset(offset).order_by(AgentModel.created_at.desc())

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def update(self, agent: Agent) -> Agent:
        """更新Agent。"""
        model = await self.session.get(AgentModel, agent.id)
        if not model:
            raise ValueError(f"Agent with ID {agent.id} not found")

        # 更新字段
        model.name = agent.name
        model.avatar = agent.avatar
        model.description = agent.description
        model.system_prompt = agent.system_prompt
        model.model_config = agent.model_config.to_dict()
        model.api_key_prefix = agent.api_key_prefix
        model.api_key_hash = agent.api_key_hash
        model.is_active = agent.is_active
        model.updated_at = agent.updated_at

        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete(self, agent_id: UUID) -> None:
        """删除Agent。"""
        model = await self.session.get(AgentModel, agent_id)
        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def count(self, is_active: Optional[bool] = None) -> int:
        """统计Agent数量。"""
        stmt = select(func.count(AgentModel.id))

        if is_active is not None:
            stmt = stmt.where(AgentModel.is_active == is_active)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    def _to_entity(self, model: AgentModel) -> Agent:
        """将模型转换为实体。"""
        return Agent(
            id=model.id,
            agent_id=AgentId(model.agent_id),
            name=model.name,
            avatar=model.avatar,
            description=model.description,
            system_prompt=model.system_prompt,
            model_config=AgentConfig.from_dict(model.model_config or {}),
            api_key_prefix=model.api_key_prefix,
            api_key_hash=model.api_key_hash,
            is_active=model.is_active,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: Agent) -> AgentModel:
        """将实体转换为模型。"""
        return AgentModel(
            id=entity.id,
            agent_id=entity.agent_id.value,
            name=entity.name,
            avatar=entity.avatar,
            description=entity.description,
            system_prompt=entity.system_prompt,
            model_config=entity.model_config.to_dict(),
            api_key_prefix=entity.api_key_prefix,
            api_key_hash=entity.api_key_hash,
            is_active=entity.is_active,
            created_by=entity.created_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
