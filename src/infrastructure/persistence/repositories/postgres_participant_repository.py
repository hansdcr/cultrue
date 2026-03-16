"""PostgreSQL Participant repository implementation."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.participant.entities.participant import Participant
from src.domain.participant.repositories.participant_repository import ParticipantRepository
from src.domain.shared.value_objects.actor import Actor
from src.infrastructure.persistence.models.participant_model import ParticipantModel


class PostgresParticipantRepository(ParticipantRepository):
    """PostgreSQL Participant仓储实现。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_actor(self, actor: Actor) -> Optional[Participant]:
        """根据Actor查找Participant。

        Args:
            actor: Actor值对象

        Returns:
            Participant实例，如果不存在返回None
        """
        if actor.is_user():
            stmt = select(ParticipantModel).where(
                ParticipantModel.user_id == actor.actor_id
            )
        else:
            stmt = select(ParticipantModel).where(
                ParticipantModel.agent_id == actor.actor_id
            )

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            return self._to_entity(model)
        return None

    async def find_or_create(self, actor: Actor) -> Participant:
        """查找或创建Participant（核心方法）。

        Args:
            actor: Actor值对象

        Returns:
            Participant实例
        """
        # 先查找
        participant = await self.find_by_actor(actor)

        # 如果不存在则创建
        if not participant:
            participant = Participant.from_actor(actor)
            participant = await self.save(participant)

        return participant

    async def save(self, participant: Participant) -> Participant:
        """保存Participant。

        Args:
            participant: Participant实例

        Returns:
            保存后的Participant实例
        """
        model = self._to_model(participant)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    def _to_entity(self, model: ParticipantModel) -> Participant:
        """将模型转换为实体。

        Args:
            model: ParticipantModel

        Returns:
            Participant实体
        """
        from src.domain.shared.enums.actor_type import ActorType

        return Participant(
            id=model.id,
            participant_type=ActorType(model.participant_type),
            user_id=model.user_id,
            agent_id=model.agent_id,
            created_at=model.created_at,
        )

    def _to_model(self, entity: Participant) -> ParticipantModel:
        """将实体转换为模型。

        Args:
            entity: Participant实体

        Returns:
            ParticipantModel
        """
        return ParticipantModel(
            id=entity.id,
            participant_type=entity.participant_type.value,
            user_id=entity.user_id,
            agent_id=entity.agent_id,
            created_at=entity.created_at,
        )
