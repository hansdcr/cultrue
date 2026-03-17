"""PostgreSQL Message repository implementation."""
from typing import List, Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.messaging.entities.message import Message
from src.domain.messaging.enums.message_type import MessageType
from src.domain.messaging.repositories.message_repository import MessageRepository
from src.domain.messaging.value_objects.conversation_id import ConversationId
from src.domain.messaging.value_objects.message_id import MessageId
from src.domain.participant.repositories.participant_repository import ParticipantRepository
from src.domain.shared.value_objects.actor import Actor
from src.infrastructure.persistence.models.message_model import MessageModel


class PostgresMessageRepository(MessageRepository):
    """PostgreSQL Message仓储实现。"""

    def __init__(
        self,
        session: AsyncSession,
        participant_repo: ParticipantRepository
    ):
        self.session = session
        self.participant_repo = participant_repo

    async def save(self, message: Message) -> Message:
        """保存消息。

        Args:
            message: 消息实体

        Returns:
            保存后的消息实体
        """
        # 1. 确保sender的Participant存在
        sender_participant = await self.participant_repo.find_or_create(message.sender)

        # 2. 保存Message
        model = MessageModel(
            id=message.id.value,
            conversation_id=message.conversation_id.value,
            sender_id=sender_participant.id,
            message_type=message.message_type.value,
            content=message.content,
            message_metadata=message.metadata,
            created_at=message.created_at
        )
        self.session.add(model)
        await self.session.flush()
        return message

    async def find_by_id(self, message_id: MessageId) -> Optional[Message]:
        """根据ID查找消息。

        Args:
            message_id: 消息ID

        Returns:
            消息实体，如果不存在返回None
        """
        stmt = select(MessageModel).where(MessageModel.id == message_id.value)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return await self._to_entity(model)

    async def find_by_conversation_id(
        self,
        conversation_id: ConversationId,
        limit: int = 50,
        offset: int = 0
    ) -> List[Message]:
        """查找会话的消息列表。

        Args:
            conversation_id: 会话ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            消息列表
        """
        stmt = (
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id.value)
            .order_by(MessageModel.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        messages = []
        for model in models:
            message = await self._to_entity(model)
            messages.append(message)

        return messages

    async def count_by_conversation_id(self, conversation_id: ConversationId) -> int:
        """统计会话的消息数量。

        Args:
            conversation_id: 会话ID

        Returns:
            消息数量
        """
        stmt = select(func.count(MessageModel.id)).where(
            MessageModel.conversation_id == conversation_id.value
        )
        result = await self.session.execute(stmt)
        count = result.scalar_one()
        return count

    async def delete(self, message_id: MessageId) -> None:
        """删除消息。

        Args:
            message_id: 消息ID
        """
        stmt = delete(MessageModel).where(MessageModel.id == message_id.value)
        await self.session.execute(stmt)
        await self.session.flush()

    async def _to_entity(self, model: MessageModel) -> Message:
        """将模型转换为实体。

        Args:
            model: MessageModel

        Returns:
            Message实体
        """
        from src.infrastructure.persistence.models.participant_model import ParticipantModel

        # 查询sender的Participant信息
        stmt = select(ParticipantModel).where(ParticipantModel.id == model.sender_id)
        result = await self.session.execute(stmt)
        participant_model = result.scalar_one()

        # 构造sender Actor
        sender = Actor(
            actor_type=participant_model.participant_type,
            actor_id=participant_model.user_id if participant_model.user_id else participant_model.agent_id
        )

        return Message(
            id=MessageId(model.id),
            conversation_id=ConversationId(model.conversation_id),
            sender=sender,
            message_type=MessageType(model.message_type),
            content=model.content,
            metadata=model.message_metadata,
            created_at=model.created_at
        )
