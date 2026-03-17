"""PostgreSQL Conversation repository implementation."""
from typing import List, Optional

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.messaging.entities.conversation import Conversation
from src.domain.messaging.enums.conversation_status import ConversationStatus
from src.domain.messaging.enums.conversation_type import ConversationType
from src.domain.messaging.repositories.conversation_repository import ConversationRepository
from src.domain.messaging.value_objects.conversation_id import ConversationId
from src.domain.participant.repositories.participant_repository import ParticipantRepository
from src.domain.shared.value_objects.actor import Actor
from src.infrastructure.persistence.models.conversation_member_model import ConversationMemberModel
from src.infrastructure.persistence.models.conversation_model import ConversationModel


class PostgresConversationRepository(ConversationRepository):
    """PostgreSQL Conversation仓储实现。"""

    def __init__(
        self,
        session: AsyncSession,
        participant_repo: ParticipantRepository
    ):
        self.session = session
        self.participant_repo = participant_repo

    async def save(self, conversation: Conversation) -> Conversation:
        """保存会话。

        Args:
            conversation: 会话实体

        Returns:
            保存后的会话实体
        """
        # 1. 保存Conversation主记录
        conv_model = ConversationModel(
            id=conversation.id.value,
            conversation_type=conversation.conversation_type.value,
            title=conversation.title,
            status=conversation.status.value,
            message_count=conversation.message_count,
            last_message_at=conversation.last_message_at,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
        self.session.add(conv_model)

        # 2. 保存members（确保Participant存在）
        for member in conversation.members:
            participant = await self.participant_repo.find_or_create(member)
            member_model = ConversationMemberModel(
                conversation_id=conversation.id.value,
                participant_id=participant.id
            )
            self.session.add(member_model)

        await self.session.flush()
        return conversation

    async def find_by_id(self, conversation_id: ConversationId) -> Optional[Conversation]:
        """根据ID查找会话。

        Args:
            conversation_id: 会话ID

        Returns:
            会话实体，如果不存在返回None
        """
        stmt = select(ConversationModel).where(
            ConversationModel.id == conversation_id.value
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        # 查询会话成员
        members = await self._get_conversation_members(conversation_id)

        return self._to_entity(model, members)

    async def find_by_actor(
        self,
        actor: Actor,
        limit: int = 20,
        offset: int = 0
    ) -> List[Conversation]:
        """查找Actor参与的会话列表。

        Args:
            actor: Actor
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            会话列表
        """
        # 1. 查找actor的Participant
        participant = await self.participant_repo.find_by_actor(actor)
        if not participant:
            return []

        # 2. 查询conversations（JOIN）
        stmt = (
            select(ConversationModel)
            .join(ConversationMemberModel)
            .where(ConversationMemberModel.participant_id == participant.id)
            .order_by(ConversationModel.last_message_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        # 3. 转换为领域实体
        conversations = []
        for model in models:
            members = await self._get_conversation_members(
                ConversationId(model.id)
            )
            conversations.append(self._to_entity(model, members))

        return conversations

    async def find_direct_conversation(
        self,
        actor1: Actor,
        actor2: Actor
    ) -> Optional[Conversation]:
        """查找两个Actor之间的一对一会话。

        Args:
            actor1: 第一个Actor
            actor2: 第二个Actor

        Returns:
            会话实体，如果不存在返回None
        """
        # 1. 查找两个actor的Participant
        participant1 = await self.participant_repo.find_by_actor(actor1)
        participant2 = await self.participant_repo.find_by_actor(actor2)

        if not participant1 or not participant2:
            return None

        # 2. 查询direct会话
        stmt = (
            select(ConversationModel)
            .join(
                ConversationMemberModel,
                ConversationModel.id == ConversationMemberModel.conversation_id
            )
            .where(
                and_(
                    ConversationModel.conversation_type == "direct",
                    ConversationMemberModel.participant_id.in_([
                        participant1.id,
                        participant2.id
                    ])
                )
            )
            .group_by(ConversationModel.id)
            .having(
                # 确保会话恰好包含这两个参与者
                select(ConversationMemberModel.id)
                .where(ConversationMemberModel.conversation_id == ConversationModel.id)
                .correlate(ConversationModel)
                .count() == 2
            )
        )

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        members = await self._get_conversation_members(ConversationId(model.id))
        return self._to_entity(model, members)

    async def add_member(self, conversation_id: ConversationId, actor: Actor) -> None:
        """向会话添加成员。

        Args:
            conversation_id: 会话ID
            actor: 要添加的Actor
        """
        participant = await self.participant_repo.find_or_create(actor)

        member_model = ConversationMemberModel(
            conversation_id=conversation_id.value,
            participant_id=participant.id
        )
        self.session.add(member_model)
        await self.session.flush()

    async def remove_member(self, conversation_id: ConversationId, actor: Actor) -> None:
        """从会话移除成员。

        Args:
            conversation_id: 会话ID
            actor: 要移除的Actor
        """
        participant = await self.participant_repo.find_by_actor(actor)
        if not participant:
            return

        stmt = delete(ConversationMemberModel).where(
            and_(
                ConversationMemberModel.conversation_id == conversation_id.value,
                ConversationMemberModel.participant_id == participant.id
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def update(self, conversation: Conversation) -> Conversation:
        """更新会话。

        Args:
            conversation: 会话实体

        Returns:
            更新后的会话实体
        """
        stmt = select(ConversationModel).where(
            ConversationModel.id == conversation.id.value
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.conversation_type = conversation.conversation_type.value
            model.title = conversation.title
            model.status = conversation.status.value
            model.message_count = conversation.message_count
            model.last_message_at = conversation.last_message_at
            model.updated_at = conversation.updated_at

            await self.session.flush()

        return conversation

    async def delete(self, conversation_id: ConversationId) -> None:
        """删除会话。

        Args:
            conversation_id: 会话ID
        """
        stmt = delete(ConversationModel).where(
            ConversationModel.id == conversation_id.value
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def _get_conversation_members(
        self,
        conversation_id: ConversationId
    ) -> List[Actor]:
        """获取会话成员列表。

        Args:
            conversation_id: 会话ID

        Returns:
            Actor列表
        """
        from src.domain.participant.entities.participant import Participant
        from src.infrastructure.persistence.models.participant_model import ParticipantModel

        stmt = (
            select(ParticipantModel)
            .join(ConversationMemberModel)
            .where(ConversationMemberModel.conversation_id == conversation_id.value)
        )
        result = await self.session.execute(stmt)
        participant_models = result.scalars().all()

        members = []
        for p_model in participant_models:
            actor = Actor(
                actor_type=p_model.participant_type,
                actor_id=p_model.user_id if p_model.user_id else p_model.agent_id
            )
            members.append(actor)

        return members

    def _to_entity(
        self,
        model: ConversationModel,
        members: List[Actor]
    ) -> Conversation:
        """将模型转换为实体。

        Args:
            model: ConversationModel
            members: 成员列表

        Returns:
            Conversation实体
        """
        return Conversation(
            id=ConversationId(model.id),
            conversation_type=ConversationType(model.conversation_type),
            status=ConversationStatus(model.status),
            members=members,
            message_count=model.message_count,
            title=model.title,
            last_message_at=model.last_message_at,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
