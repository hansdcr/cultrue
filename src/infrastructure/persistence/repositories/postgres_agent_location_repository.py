"""PostgreSQL Agent地理位置仓储实现。"""
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_SetSRID, ST_MakePoint

from src.domain.map.entities.agent_location import AgentLocation
from src.domain.map.repositories.agent_location_repository import AgentLocationRepository
from src.domain.agent.entities.agent import Agent
from src.domain.agent.repositories.agent_repository import AgentRepository
from src.infrastructure.persistence.models.agent_location_model import AgentLocationModel
from src.infrastructure.persistence.models.agent_model import AgentModel


class PostgresAgentLocationRepository(AgentLocationRepository):
    """PostgreSQL Agent地理位置仓储实现。"""

    def __init__(
        self,
        session: AsyncSession,
        agent_repo: AgentRepository
    ):
        self.session = session
        self.agent_repo = agent_repo

    async def save(self, location: AgentLocation) -> AgentLocation:
        """保存Agent位置。"""
        model = self._to_model(location)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def find_by_id(self, location_id: UUID) -> Optional[AgentLocation]:
        """根据ID查找位置。"""
        stmt = select(AgentLocationModel).where(AgentLocationModel.id == location_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_agent_id(self, agent_id: UUID) -> List[AgentLocation]:
        """查找Agent的所有位置。"""
        stmt = (
            select(AgentLocationModel)
            .where(AgentLocationModel.agent_id == agent_id)
            .order_by(AgentLocationModel.display_order)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def find_nearby(
        self,
        latitude: float,
        longitude: float,
        radius: int,
        limit: int = 10,
        only_active: bool = True
    ) -> List[AgentLocation]:
        """查找周边位置（使用PostGIS）。"""
        # 使用PostGIS的ST_DWithin函数进行空间查询
        point = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)

        stmt = select(AgentLocationModel).where(
            ST_DWithin(AgentLocationModel.location, point, radius)
        )

        if only_active:
            stmt = stmt.where(AgentLocationModel.is_active == True)

        # 按距离排序
        stmt = stmt.order_by(
            ST_Distance(AgentLocationModel.location, point)
        ).limit(limit)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def find_nearby_with_agents(
        self,
        latitude: float,
        longitude: float,
        radius: int,
        limit: int = 10,
        only_active: bool = True
    ) -> List[Tuple[AgentLocation, Agent, float]]:
        """查找周边位置并返回Agent信息和距离。

        Returns:
            List[Tuple[AgentLocation, Agent, distance]]
        """
        # 创建点
        point = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)

        # JOIN查询
        stmt = (
            select(
                AgentLocationModel,
                AgentModel,
                ST_Distance(AgentLocationModel.location, point).label('distance')
            )
            .join(AgentModel, AgentLocationModel.agent_id == AgentModel.id)
            .where(ST_DWithin(AgentLocationModel.location, point, radius))
        )

        if only_active:
            stmt = stmt.where(AgentLocationModel.is_active == True)

        stmt = stmt.order_by('distance').limit(limit)

        result = await self.session.execute(stmt)
        rows = result.all()

        return [
            (
                self._to_entity(location_model),
                self.agent_repo._to_entity(agent_model),
                float(distance)
            )
            for location_model, agent_model, distance in rows
        ]

    async def update(self, location: AgentLocation) -> AgentLocation:
        """更新位置。"""
        model = await self.session.get(AgentLocationModel, location.id)
        if not model:
            raise ValueError(f"AgentLocation with ID {location.id} not found")

        # 更新字段
        model.agent_id = location.agent_id
        model.latitude = location.latitude
        model.longitude = location.longitude
        model.address = location.address
        model.is_active = location.is_active
        model.display_order = location.display_order
        model.metadata = location.metadata
        model.updated_at = location.updated_at

        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete(self, location_id: UUID) -> None:
        """删除位置。"""
        model = await self.session.get(AgentLocationModel, location_id)
        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def count_by_agent_id(self, agent_id: UUID) -> int:
        """统计Agent的位置数量。"""
        stmt = select(func.count(AgentLocationModel.id)).where(
            AgentLocationModel.agent_id == agent_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    def _to_entity(self, model: AgentLocationModel) -> AgentLocation:
        """将模型转换为实体。"""
        return AgentLocation(
            id=model.id,
            agent_id=model.agent_id,
            latitude=float(model.latitude),
            longitude=float(model.longitude),
            address=model.address,
            is_active=model.is_active,
            display_order=model.display_order,
            metadata=model.metadata or {},
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, entity: AgentLocation) -> AgentLocationModel:
        """将实体转换为模型。"""
        return AgentLocationModel(
            id=entity.id,
            agent_id=entity.agent_id,
            latitude=entity.latitude,
            longitude=entity.longitude,
            address=entity.address,
            is_active=entity.is_active,
            display_order=entity.display_order,
            metadata=entity.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
