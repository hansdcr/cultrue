"""PostgreSQL Contact repository implementation."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.contact.entities.contact import Contact
from src.domain.contact.enums.contact_type import ContactType
from src.domain.contact.repositories.contact_repository import ContactRepository
from src.domain.participant.repositories.participant_repository import ParticipantRepository
from src.domain.shared.value_objects.actor import Actor
from src.infrastructure.persistence.models.contact_model import ContactModel


class PostgresContactRepository(ContactRepository):
    """PostgreSQL Contact仓储实现。"""

    def __init__(
        self,
        session: AsyncSession,
        participant_repo: ParticipantRepository
    ):
        self.session = session
        self.participant_repo = participant_repo

    async def save(self, contact: Contact) -> Contact:
        """保存Contact。"""
        # 确保Participant存在
        owner_participant = await self.participant_repo.find_or_create(contact.owner)
        target_participant = await self.participant_repo.find_or_create(contact.target)

        # 创建ContactModel
        model = ContactModel(
            id=contact.id,
            owner_id=owner_participant.id,
            target_id=target_participant.id,
            contact_type=contact.contact_type.value,
            alias=contact.alias,
            is_favorite=contact.is_favorite,
            last_interaction_at=contact.last_interaction_at,
            created_at=contact.created_at,
        )

        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return await self._to_entity(model)

    async def find_by_id(self, contact_id: UUID) -> Optional[Contact]:
        """根据ID查找Contact。"""
        stmt = select(ContactModel).where(ContactModel.id == contact_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return await self._to_entity(model) if model else None

    async def find_by_owner_and_target(
        self,
        owner: Actor,
        target: Actor
    ) -> Optional[Contact]:
        """根据owner和target查找Contact。"""
        # 查找Participant
        owner_participant = await self.participant_repo.find_by_actor(owner)
        target_participant = await self.participant_repo.find_by_actor(target)

        if not owner_participant or not target_participant:
            return None

        stmt = select(ContactModel).where(
            ContactModel.owner_id == owner_participant.id,
            ContactModel.target_id == target_participant.id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return await self._to_entity(model) if model else None

    async def find_by_owner(
        self,
        owner: Actor,
        contact_type: Optional[ContactType] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Contact]:
        """查找owner的所有联系人。"""
        # 查找owner的Participant
        owner_participant = await self.participant_repo.find_by_actor(owner)
        if not owner_participant:
            return []

        stmt = select(ContactModel).where(ContactModel.owner_id == owner_participant.id)

        if contact_type:
            stmt = stmt.where(ContactModel.contact_type == contact_type.value)

        stmt = stmt.limit(limit).offset(offset).order_by(ContactModel.created_at.desc())

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        contacts = []
        for model in models:
            contact = await self._to_entity(model)
            if contact:
                contacts.append(contact)
        return contacts

    async def update(self, contact: Contact) -> Contact:
        """更新Contact。"""
        model = await self.session.get(ContactModel, contact.id)
        if not model:
            raise ValueError(f"Contact with ID {contact.id} not found")

        # 更新字段
        model.contact_type = contact.contact_type.value
        model.alias = contact.alias
        model.is_favorite = contact.is_favorite
        model.last_interaction_at = contact.last_interaction_at

        await self.session.flush()
        await self.session.refresh(model)
        return await self._to_entity(model)

    async def delete(self, contact_id: UUID) -> None:
        """删除Contact。"""
        model = await self.session.get(ContactModel, contact_id)
        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def count_by_owner(
        self,
        owner: Actor,
        contact_type: Optional[ContactType] = None
    ) -> int:
        """统计owner的联系人数量。"""
        # 查找owner的Participant
        owner_participant = await self.participant_repo.find_by_actor(owner)
        if not owner_participant:
            return 0

        stmt = select(func.count(ContactModel.id)).where(
            ContactModel.owner_id == owner_participant.id
        )

        if contact_type:
            stmt = stmt.where(ContactModel.contact_type == contact_type.value)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def _to_entity(self, model: ContactModel) -> Optional[Contact]:
        """将模型转换为实体。"""
        # 查找owner和target的Participant
        from src.infrastructure.persistence.models.participant_model import ParticipantModel

        owner_stmt = select(ParticipantModel).where(ParticipantModel.id == model.owner_id)
        owner_result = await self.session.execute(owner_stmt)
        owner_model = owner_result.scalar_one_or_none()

        target_stmt = select(ParticipantModel).where(ParticipantModel.id == model.target_id)
        target_result = await self.session.execute(target_stmt)
        target_model = target_result.scalar_one_or_none()

        if not owner_model or not target_model:
            return None

        # 转换为Actor
        from src.domain.participant.entities.participant import Participant
        from src.domain.shared.enums.actor_type import ActorType

        owner_participant = Participant(
            id=owner_model.id,
            participant_type=ActorType(owner_model.participant_type),
            user_id=owner_model.user_id,
            agent_id=owner_model.agent_id,
            created_at=owner_model.created_at,
        )
        target_participant = Participant(
            id=target_model.id,
            participant_type=ActorType(target_model.participant_type),
            user_id=target_model.user_id,
            agent_id=target_model.agent_id,
            created_at=target_model.created_at,
        )

        return Contact(
            id=model.id,
            owner=owner_participant.to_actor(),
            target=target_participant.to_actor(),
            contact_type=ContactType(model.contact_type),
            alias=model.alias,
            is_favorite=model.is_favorite,
            last_interaction_at=model.last_interaction_at,
            created_at=model.created_at,
        )
