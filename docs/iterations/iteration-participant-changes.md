# 迭代6、7、8关键修改 - Participant中间表方案

> 本文档说明采用Participant中间表后，迭代6、7、8的关键修改点

## 📋 修改概览

### 核心变化
- **数据库层**：添加participants表，使用外键约束
- **领域层**：保持Actor值对象，新增Participant实体（仅用于数据库映射）
- **仓储层**：自动管理Participant，实现Actor ↔ Participant转换
- **应用层**：移除ActorValidationService，代码更简洁

---

## 🔧 迭代6修改

### 1. 新增Participant领域层

#### 文件：`src/domain/participant/entities/participant.py`

```python
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional
from src.domain.shared.value_objects.actor import Actor, ActorType

@dataclass
class Participant:
    """Participant实体（数据库映射层）。

    用于保证数据完整性的中间表实体。
    应用层使用Actor，仓储层使用Participant。
    """
    id: UUID
    participant_type: ActorType
    user_id: Optional[UUID]
    agent_id: Optional[UUID]
    created_at: datetime

    @classmethod
    def from_actor(cls, actor: Actor) -> "Participant":
        """从Actor创建Participant。"""
        if actor.is_user():
            return cls(
                id=uuid4(),
                participant_type=ActorType.USER,
                user_id=actor.actor_id,
                agent_id=None,
                created_at=datetime.now(timezone.utc)
            )
        else:
            return cls(
                id=uuid4(),
                participant_type=ActorType.AGENT,
                user_id=None,
                agent_id=actor.actor_id,
                created_at=datetime.now(timezone.utc)
            )

    def to_actor(self) -> Actor:
        """转换为Actor。"""
        if self.participant_type == ActorType.USER:
            return Actor.from_user(self.user_id)
        else:
            return Actor.from_agent(self.agent_id)

    def matches_actor(self, actor: Actor) -> bool:
        """检查是否匹配指定的Actor。"""
        if actor.is_user():
            return self.participant_type == ActorType.USER and self.user_id == actor.actor_id
        else:
            return self.participant_type == ActorType.AGENT and self.agent_id == actor.actor_id
```

#### 文件：`src/domain/participant/repositories/participant_repository.py`

```python
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from src.domain.participant.entities.participant import Participant
from src.domain.shared.value_objects.actor import Actor

class ParticipantRepository(ABC):
    """Participant仓储接口。"""

    @abstractmethod
    async def find_by_id(self, participant_id: UUID) -> Optional[Participant]:
        """根据ID查找Participant。"""
        pass

    @abstractmethod
    async def find_by_actor(self, actor: Actor) -> Optional[Participant]:
        """根据Actor查找Participant。"""
        pass

    @abstractmethod
    async def find_or_create(self, actor: Actor) -> Participant:
        """查找或创建Participant。

        如果不存在，自动创建。这是核心方法。
        """
        pass

    @abstractmethod
    async def save(self, participant: Participant) -> Participant:
        """保存Participant。"""
        pass
```

### 2. 更新数据库表结构

#### 文件：`migrations/versions/xxx_create_participants_and_contacts.py`

```python
"""create participants and contacts tables

Revision ID: xxx
"""

def upgrade():
    # 1. 创建participants表
    op.create_table(
        'participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('participant_type', sa.String(20), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        # 外键约束
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),

        # CHECK约束
        sa.CheckConstraint(
            "(participant_type = 'user' AND user_id IS NOT NULL AND agent_id IS NULL) OR "
            "(participant_type = 'agent' AND agent_id IS NOT NULL AND user_id IS NULL)",
            name='check_participant_type'
        ),

        # 唯一约束
        sa.UniqueConstraint('user_id', name='unique_user_participant'),
        sa.UniqueConstraint('agent_id', name='unique_agent_participant')
    )

    # 索引
    op.create_index('idx_participants_type', 'participants', ['participant_type'])
    op.create_index('idx_participants_user_id', 'participants', ['user_id'])
    op.create_index('idx_participants_agent_id', 'participants', ['agent_id'])

    # 2. 创建contacts表（使用外键）
    op.create_table(
        'contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contact_type', sa.String(20), server_default='friend'),
        sa.Column('alias', sa.String(100), nullable=True),
        sa.Column('is_favorite', sa.Boolean, server_default='false'),
        sa.Column('last_interaction_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        # 外键约束
        sa.ForeignKeyConstraint(['owner_id'], ['participants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_id'], ['participants.id'], ondelete='CASCADE'),

        # 唯一约束
        sa.UniqueConstraint('owner_id', 'target_id', name='unique_contact')
    )

    # 索引
    op.create_index('idx_contacts_owner_id', 'contacts', ['owner_id'])
    op.create_index('idx_contacts_target_id', 'contacts', ['target_id'])
    op.create_index('idx_contacts_type', 'contacts', ['contact_type'])
```

### 3. 实现ParticipantRepository

#### 文件：`src/infrastructure/persistence/repositories/postgres_participant_repository.py`

```python
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.participant.entities.participant import Participant
from src.domain.participant.repositories.participant_repository import ParticipantRepository
from src.domain.shared.value_objects.actor import Actor
from src.infrastructure.persistence.models.participant_model import ParticipantModel

class PostgresParticipantRepository(ParticipantRepository):
    """Participant仓储实现。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, participant_id: UUID) -> Optional[Participant]:
        result = await self.session.execute(
            select(ParticipantModel).where(ParticipantModel.id == participant_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_actor(self, actor: Actor) -> Optional[Participant]:
        """根据Actor查找Participant。"""
        if actor.is_user():
            result = await self.session.execute(
                select(ParticipantModel).where(
                    ParticipantModel.user_id == actor.actor_id
                )
            )
        else:
            result = await self.session.execute(
                select(ParticipantModel).where(
                    ParticipantModel.agent_id == actor.actor_id
                )
            )

        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_or_create(self, actor: Actor) -> Participant:
        """查找或创建Participant（核心方法）。"""
        # 1. 先尝试查找
        participant = await self.find_by_actor(actor)

        # 2. 不存在则创建
        if not participant:
            participant = Participant.from_actor(actor)
            model = self._to_model(participant)
            self.session.add(model)
            await self.session.flush()  # 立即刷新以获取ID
            await self.session.refresh(model)
            participant = self._to_entity(model)

        return participant

    async def save(self, participant: Participant) -> Participant:
        model = self._to_model(participant)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    def _to_entity(self, model: ParticipantModel) -> Participant:
        """模型转实体。"""
        return Participant(
            id=model.id,
            participant_type=model.participant_type,
            user_id=model.user_id,
            agent_id=model.agent_id,
            created_at=model.created_at
        )

    def _to_model(self, entity: Participant) -> ParticipantModel:
        """实体转模型。"""
        return ParticipantModel(
            id=entity.id,
            participant_type=entity.participant_type.value,
            user_id=entity.user_id,
            agent_id=entity.agent_id,
            created_at=entity.created_at
        )
```

### 4. 更新ContactRepository

#### 文件：`src/infrastructure/persistence/repositories/postgres_contact_repository.py`

```python
class PostgresContactRepository(ContactRepository):
    """Contact仓储实现。"""

    def __init__(
        self,
        session: AsyncSession,
        participant_repo: ParticipantRepository  # 注入
    ):
        self.session = session
        self.participant_repo = participant_repo

    async def save(self, contact: Contact) -> Contact:
        # 1. 确保owner和target的Participant存在
        owner_participant = await self.participant_repo.find_or_create(contact.owner)
        target_participant = await self.participant_repo.find_or_create(contact.target)

        # 2. 创建ContactModel（使用participant_id）
        model = ContactModel(
            id=contact.id,
            owner_id=owner_participant.id,  # 使用participant.id
            target_id=target_participant.id,  # 使用participant.id
            contact_type=contact.contact_type.value,
            alias=contact.alias,
            is_favorite=contact.is_favorite,
            last_interaction_at=contact.last_interaction_at,
            created_at=contact.created_at
        )

        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        return contact

    async def find_by_owner(self, owner: Actor) -> List[Contact]:
        # 1. 查找owner的Participant
        owner_participant = await self.participant_repo.find_by_actor(owner)
        if not owner_participant:
            return []

        # 2. 查询contacts（JOIN target_participant）
        result = await self.session.execute(
            select(ContactModel)
            .where(ContactModel.owner_id == owner_participant.id)
            .options(joinedload(ContactModel.target_participant))
        )
        models = result.scalars().all()

        # 3. 转换为领域实体（使用Actor）
        contacts = []
        for model in models:
            contact = Contact(
                id=model.id,
                owner=owner,  # 直接使用传入的owner
                target=model.target_participant.to_actor(),  # 转换为Actor
                contact_type=ContactType(model.contact_type),
                alias=model.alias,
                is_favorite=model.is_favorite,
                last_interaction_at=model.last_interaction_at,
                created_at=model.created_at
            )
            contacts.append(contact)

        return contacts
```

### 5. 移除ActorValidationService

删除以下文件：
- ~~`src/application/shared/services/actor_validation_service.py`~~

更新应用层Command Handler，移除validate_actors调用。

---

## 🔧 迭代7修改

### 1. 更新数据库表结构

#### conversation_members表

```sql
CREATE TABLE conversation_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    participant_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,  -- 使用外键
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_read_at TIMESTAMP WITH TIME ZONE,
    is_muted BOOLEAN DEFAULT FALSE,
    UNIQUE(conversation_id, participant_id)
);

CREATE INDEX idx_conversation_members_conversation_id ON conversation_members(conversation_id);
CREATE INDEX idx_conversation_members_participant_id ON conversation_members(participant_id);
```

#### messages表

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,  -- 使用外键
    message_type VARCHAR(20) DEFAULT 'text',
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_sender_id ON messages(sender_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

### 2. 更新ConversationRepository

```python
class PostgresConversationRepository(ConversationRepository):
    def __init__(
        self,
        session: AsyncSession,
        participant_repo: ParticipantRepository  # 注入
    ):
        self.session = session
        self.participant_repo = participant_repo

    async def save(self, conversation: Conversation) -> Conversation:
        # 1. 保存Conversation主记录
        conv_model = ConversationModel(
            id=conversation.id,
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
                conversation_id=conversation.id,
                participant_id=participant.id  # 使用participant.id
            )
            self.session.add(member_model)

        await self.session.flush()
        return conversation

    async def find_by_actor(self, actor: Actor, limit: int, offset: int) -> List[Conversation]:
        # 1. 查找actor的Participant
        participant = await self.participant_repo.find_by_actor(actor)
        if not participant:
            return []

        # 2. 查询conversations
        result = await self.session.execute(
            select(ConversationModel)
            .join(ConversationMemberModel)
            .where(ConversationMemberModel.participant_id == participant.id)
            .order_by(ConversationModel.last_message_at.desc())
            .limit(limit)
            .offset(offset)
        )
        conv_models = result.scalars().all()

        # 3. 转换为领域实体
        conversations = []
        for conv_model in conv_models:
            # 查询所有members
            members_result = await self.session.execute(
                select(ConversationMemberModel)
                .where(ConversationMemberModel.conversation_id == conv_model.id)
                .options(joinedload(ConversationMemberModel.participant))
            )
            member_models = members_result.scalars().all()

            # 转换members为Actor列表
            members = [
                m.participant.to_actor() for m in member_models
            ]

            conversation = Conversation(
                id=conv_model.id,
                conversation_type=ConversationType(conv_model.conversation_type),
                title=conv_model.title,
                status=ConversationStatus(conv_model.status),
                members=members,  # Actor列表
                message_count=conv_model.message_count,
                last_message_at=conv_model.last_message_at,
                created_at=conv_model.created_at,
                updated_at=conv_model.updated_at
            )
            conversations.append(conversation)

        return conversations
```

### 3. 更新MessageRepository

```python
class PostgresMessageRepository(MessageRepository):
    def __init__(
        self,
        session: AsyncSession,
        participant_repo: ParticipantRepository  # 注入
    ):
        self.session = session
        self.participant_repo = participant_repo

    async def save(self, message: Message) -> Message:
        # 1. 确保sender的Participant存在
        sender_participant = await self.participant_repo.find_or_create(message.sender)

        # 2. 保存Message
        model = MessageModel(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=sender_participant.id,  # 使用participant.id
            message_type=message.message_type.value,
            content=message.content,
            metadata=message.metadata,
            created_at=message.created_at
        )

        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        return message

    async def find_by_conversation_id(
        self,
        conversation_id: UUID,
        limit: int,
        offset: int
    ) -> List[Message]:
        result = await self.session.execute(
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .options(joinedload(MessageModel.sender_participant))
            .order_by(MessageModel.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()

        messages = []
        for model in models:
            message = Message(
                id=model.id,
                conversation_id=model.conversation_id,
                sender=model.sender_participant.to_actor(),  # 转换为Actor
                message_type=MessageType(model.message_type),
                content=model.content,
                metadata=model.metadata,
                created_at=model.created_at
            )
            messages.append(message)

        return messages
```

---

## 🔧 迭代8修改

### 1. 移除ActorValidationService

删除所有引用：
```python
# 原代码
class CreateConversationCommandHandler:
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        actor_validation_service: ActorValidationService  # 删除
    ):
        ...

    async def handle(self, command: CreateConversationCommand):
        # 删除这行
        await self.actor_validation_service.validate_actors(command.members)

        conversation = Conversation.create_direct(...)
        return await self.conversation_repo.save(conversation)

# 新代码
class CreateConversationCommandHandler:
    def __init__(
        self,
        conversation_repo: ConversationRepository
    ):
        ...

    async def handle(self, command: CreateConversationCommand):
        # 无需验证，仓储层会自动处理
        conversation = Conversation.create_direct(...)
        return await self.conversation_repo.save(conversation)
```

### 2. 简化依赖注入

```python
# src/interfaces/api/dependencies.py

# 删除
# def get_actor_validation_service() -> ActorValidationService:
#     ...

# 保持
async def get_current_actor(request: Request) -> Actor:
    """获取当前认证的Actor。"""
    if not hasattr(request.state, "actor"):
        raise UnauthorizedException("Not authenticated")
    return request.state.actor
```

### 3. 更新API文档

API请求/响应格式保持不变，但内部实现更简洁：

```python
@router.post("/api/conversations", status_code=201)
async def create_conversation(
    request: CreateConversationRequest,
    current_actor: Actor = Depends(get_current_actor),
    handler: CreateConversationCommandHandler = Depends(...)
):
    """创建会话。

    内部会自动：
    1. 确保所有members的Participant存在
    2. 使用外键保证数据完整性
    3. 如果Actor不存在，数据库会抛出外键约束错误
    """
    command = CreateConversationCommand(
        conversation_type=request.conversation_type,
        members=[
            Actor(actor_type=ActorType(m.actor_type), actor_id=m.actor_id)
            for m in request.members
        ],
        title=request.title,
        creator=current_actor
    )

    result = await handler.handle(command)
    return ApiResponse(code=201, data=result.dict())
```

---

## ✅ 总结

### 关键变化

1. **新增Participant实体和仓储**
   - 仅用于数据库映射
   - 应用层透明

2. **数据库表使用外键**
   - participants表
   - contacts、conversation_members、messages引用participants

3. **仓储层自动管理**
   - find_or_create自动创建Participant
   - Actor ↔ Participant自动转换

4. **应用层简化**
   - 移除ActorValidationService
   - 无需手动验证

### 优势

- ✅ 数据完整性由数据库保证
- ✅ 应用层代码更简洁
- ✅ 性能更好（减少验证查询）
- ✅ 易于调试（数据库层面就能发现问题）

---

**更新日期**: 2026-03-16
**适用迭代**: 迭代6、7、8
