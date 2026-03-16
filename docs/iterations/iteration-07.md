# 迭代7: 消息系统-数据模型

> 设计和实现支持多类型Actor的消息系统数据模型

## 📋 迭代信息

- **迭代编号**: 7
- **预计时间**: 1-2天
- **当前状态**: 🟡 计划中
- **依赖迭代**: 迭代6 ✅
- **开始日期**: 待定

## 🎯 迭代目标

设计和实现支持**User ↔ User**、**User ↔ Agent**、**Agent ↔ Agent**以及**群聊**的统一消息系统数据模型。

## 💡 设计理念

**双层抽象架构（与迭代6保持一致）**：
- **领域层**：使用Actor值对象统一抽象User和Agent
- **数据库层**：使用Participant中间表，通过外键约束保证数据完整性
- **仓储层**：自动管理Actor ↔ Participant转换，对应用层透明

### 设计优势

- ✅ 支持User ↔ User通信
- ✅ 支持User ↔ Agent通信
- ✅ 支持Agent ↔ Agent通信
- ✅ 支持群聊（多人/多Agent）
- ✅ 数据完整性由数据库外键保证
- ✅ 符合DDD设计原则
- ✅ 与迭代6的Participant架构完全一致

## 📝 任务清单

### 1. Actor值对象（复用迭代6）

**说明**: 直接复用迭代6中定义的Actor值对象，无需重复创建。

**引用位置**:
- `src/domain/shared/value_objects/actor.py`
- `src/domain/shared/enums/actor_type.py`

**Actor设计**:
```python
from enum import Enum
from dataclasses import dataclass
from uuid import UUID

class ActorType(str, Enum):
    """Actor类型枚举。"""
    USER = "user"
    AGENT = "agent"

@dataclass(frozen=True)
class Actor:
    """Actor值对象（统一User和Agent的抽象）。"""
    actor_type: ActorType
    actor_id: UUID

    @classmethod
    def from_user(cls, user_id: UUID) -> "Actor":
        """从User创建Actor。"""
        return cls(actor_type=ActorType.USER, actor_id=user_id)

    @classmethod
    def from_agent(cls, agent_id: UUID) -> "Actor":
        """从Agent创建Actor。"""
        return cls(actor_type=ActorType.AGENT, actor_id=agent_id)

    def is_user(self) -> bool:
        return self.actor_type == ActorType.USER

    def is_agent(self) -> bool:
        return self.actor_type == ActorType.AGENT
```

### 2. Conversation领域层

**任务**:
- [ ] 创建ConversationType枚举
- [ ] 创建ConversationStatus枚举
- [ ] 创建ConversationId值对象
- [ ] 创建Conversation实体
- [ ] 创建ConversationRepository接口

**交付物**:
- `src/domain/messaging/enums/conversation_type.py`
- `src/domain/messaging/enums/conversation_status.py`
- `src/domain/messaging/value_objects/conversation_id.py`
- `src/domain/messaging/entities/conversation.py`
- `src/domain/messaging/repositories/conversation_repository.py`

**设计要点**:
```python
# ConversationType枚举
class ConversationType(str, Enum):
    DIRECT = "direct"  # 一对一
    GROUP = "group"    # 群聊

# ConversationStatus枚举
class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

# Conversation实体
from src.domain.shared.value_objects.actor import Actor

class Conversation:
    """会话实体。"""
    id: UUID
    conversation_type: ConversationType
    title: Optional[str]
    status: ConversationStatus
    members: List[Actor]  # 使用Actor值对象
    message_count: int
    last_message_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    def add_member(self, actor: Actor) -> None:
        """添加成员。"""
        if actor not in self.members:
            self.members.append(actor)

    def remove_member(self, actor: Actor) -> None:
        """移除成员。"""
        if actor in self.members:
            self.members.remove(actor)

    def has_member(self, actor: Actor) -> bool:
        """检查是否包含指定成员。"""
        return actor in self.members

    def is_direct(self) -> bool:
        return self.conversation_type == ConversationType.DIRECT

    def is_group(self) -> bool:
        return self.conversation_type == ConversationType.GROUP

    @classmethod
    def create_direct(cls, actor1: Actor, actor2: Actor) -> "Conversation":
        """创建一对一会话。"""
        return cls(
            id=uuid4(),
            conversation_type=ConversationType.DIRECT,
            title=None,
            status=ConversationStatus.ACTIVE,
            members=[actor1, actor2],
            message_count=0,
            last_message_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    @classmethod
    def create_group(cls, title: str, members: List[Actor]) -> "Conversation":
        """创建群聊。"""
        return cls(
            id=uuid4(),
            conversation_type=ConversationType.GROUP,
            title=title,
            status=ConversationStatus.ACTIVE,
            members=members,
            message_count=0,
            last_message_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
```

### 3. Message领域层

**任务**:
- [ ] 创建MessageType枚举
- [ ] 创建MessageId值对象
- [ ] 创建Message实体
- [ ] 创建MessageRepository接口

**交付物**:
- `src/domain/messaging/enums/message_type.py`
- `src/domain/messaging/value_objects/message_id.py`
- `src/domain/messaging/entities/message.py`
- `src/domain/messaging/repositories/message_repository.py`

**设计要点**:
```python
# MessageType枚举
class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"

# Message实体
from src.domain.shared.value_objects.actor import Actor

class Message:
    """消息实体。"""
    id: UUID
    conversation_id: UUID
    sender: Actor  # 使用Actor值对象
    message_type: MessageType
    content: str
    metadata: Optional[dict]
    created_at: datetime

    def is_from(self, actor: Actor) -> bool:
        """判断消息是否来自指定Actor。"""
        return self.sender == actor

    @classmethod
    def create(
        cls,
        conversation_id: UUID,
        sender: Actor,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[dict] = None
    ) -> "Message":
        """创建消息。"""
        return cls(
            id=uuid4(),
            conversation_id=conversation_id,
            sender=sender,
            message_type=message_type,
            content=content,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
```

### 4. 数据库模型

**任务**:
- [ ] 创建ConversationModel
- [ ] 创建ConversationMemberModel（关联表）
- [ ] 创建MessageModel
- [ ] 创建数据库迁移脚本

**交付物**:
- `src/infrastructure/persistence/models/conversation_model.py`
- `src/infrastructure/persistence/models/conversation_member_model.py`
- `src/infrastructure/persistence/models/message_model.py`
- `migrations/versions/xxx_create_messaging_tables.py`

**数据库表设计**:
```sql
-- conversations表（会话）
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_type VARCHAR(20) DEFAULT 'direct',
    title VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- conversation_members表（会话成员，使用外键引用participants）⭐ 修改
CREATE TABLE conversation_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    participant_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,  -- ⭐ 外键
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_read_at TIMESTAMP WITH TIME ZONE,
    is_muted BOOLEAN DEFAULT FALSE,
    UNIQUE(conversation_id, participant_id)
);

-- messages表（消息，使用外键引用participants）⭐ 修改
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,  -- ⭐ 外键
    message_type VARCHAR(20) DEFAULT 'text',
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Direct会话去重约束 ⭐ 新增
-- 为Direct会话创建唯一约束，防止并发创建重复会话
CREATE UNIQUE INDEX idx_direct_conversation_members
ON conversation_members (
    LEAST(participant_id, (
        SELECT cm2.participant_id
        FROM conversation_members cm2
        WHERE cm2.conversation_id = conversation_members.conversation_id
        AND cm2.participant_id != conversation_members.participant_id
        LIMIT 1
    )),
    GREATEST(participant_id, (
        SELECT cm2.participant_id
        FROM conversation_members cm2
        WHERE cm2.conversation_id = conversation_members.conversation_id
        AND cm2.participant_id != conversation_members.participant_id
        LIMIT 1
    ))
)
WHERE (
    SELECT conversation_type FROM conversations
    WHERE id = conversation_members.conversation_id
) = 'direct';

-- 索引
CREATE INDEX idx_conversations_type ON conversations(conversation_type);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_last_message_at ON conversations(last_message_at DESC);
CREATE INDEX idx_conversation_members_conversation_id ON conversation_members(conversation_id);
CREATE INDEX idx_conversation_members_participant_id ON conversation_members(participant_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_sender_id ON messages(sender_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

**设计说明**:
- **使用Participant中间表**: conversation_members和messages引用participants.id
- **外键约束**: 数据库层面保证数据完整性
- **Direct会话去重**: 通过唯一索引防止并发创建重复会话
- **仓储层自动管理**: 使用find_or_create模式确保Participant存在

### 5. 仓储实现

**任务**:
- [ ] 创建PostgresConversationRepository
- [ ] 创建PostgresMessageRepository
- [ ] 实现实体与模型的转换方法
- [ ] 实现Actor的序列化/反序列化

**交付物**:
- `src/infrastructure/persistence/repositories/postgres_conversation_repository.py`
- `src/infrastructure/persistence/repositories/postgres_message_repository.py`

**仓储方法**:
```python
# ConversationRepository
class ConversationRepository(ABC):
    async def save(self, conversation: Conversation) -> Conversation
    async def find_by_id(self, conversation_id: UUID) -> Optional[Conversation]
    async def find_by_actor(self, actor: Actor, limit: int = 20, offset: int = 0) -> List[Conversation]
    async def find_direct_conversation(self, actor1: Actor, actor2: Actor) -> Optional[Conversation]
    async def add_member(self, conversation_id: UUID, actor: Actor) -> None
    async def remove_member(self, conversation_id: UUID, actor: Actor) -> None
    async def update(self, conversation: Conversation) -> Conversation
    async def delete(self, conversation_id: UUID) -> None

# MessageRepository
class MessageRepository(ABC):
    async def save(self, message: Message) -> Message
    async def find_by_id(self, message_id: UUID) -> Optional[Message]
    async def find_by_conversation_id(
        self,
        conversation_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Message]
    async def count_by_conversation_id(self, conversation_id: UUID) -> int
    async def delete(self, message_id: UUID) -> None
```

**仓储实现要点**:
```python
# PostgresConversationRepository
class PostgresConversationRepository(ConversationRepository):
    def __init__(
        self,
        session: AsyncSession,
        participant_repo: ParticipantRepository  # ⭐ 注入
    ):
        self.session = session
        self.participant_repo = participant_repo

    async def save(self, conversation: Conversation) -> Conversation:
        # 1. 保存Conversation主记录
        conv_model = ConversationModel(...)
        self.session.add(conv_model)

        # 2. 保存members（确保Participant存在）
        for member in conversation.members:
            participant = await self.participant_repo.find_or_create(member)
            member_model = ConversationMemberModel(
                conversation_id=conversation.id,
                participant_id=participant.id  # ⭐ 使用participant.id
            )
            self.session.add(member_model)

        await self.session.flush()
        return conversation

    async def find_by_actor(self, actor: Actor, limit: int, offset: int) -> List[Conversation]:
        # 1. 查找actor的Participant
        participant = await self.participant_repo.find_by_actor(actor)
        if not participant:
            return []

        # 2. 查询conversations（JOIN）
        result = await self.session.execute(
            select(ConversationModel)
            .join(ConversationMemberModel)
            .where(ConversationMemberModel.participant_id == participant.id)
            .order_by(ConversationModel.last_message_at.desc())
            .limit(limit).offset(offset)
        )
        # 3. 转换为领域实体（使用Actor）
        ...

# PostgresMessageRepository
class PostgresMessageRepository(MessageRepository):
    def __init__(
        self,
        session: AsyncSession,
        participant_repo: ParticipantRepository  # ⭐ 注入
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
            sender_id=sender_participant.id,  # ⭐ 使用participant.id
            ...
        )
        self.session.add(model)
        await self.session.flush()
        return message
```

### 6. 测试

**任务**:
- [ ] 编写Conversation实体单元测试
- [ ] 编写Message实体单元测试
- [ ] 编写仓储集成测试
- [ ] 测试数据库迁移
- [ ] 测试多种通信场景

**交付物**:
- `tests/unit/domain/messaging/test_conversation_entity.py`
- `tests/unit/domain/messaging/test_message_entity.py`
- `tests/integration/test_conversation_repository.py`
- `tests/integration/test_message_repository.py`

**测试场景**:
```python
# 测试场景1: User ↔ User
async def test_user_to_user_conversation():
    user1 = Actor.from_user(user1_id)
    user2 = Actor.from_user(user2_id)
    conversation = Conversation.create_direct(user1, user2)
    message = Message.create(conversation.id, user1, "Hello Bob!")

    assert conversation.is_direct()
    assert conversation.has_member(user1)
    assert conversation.has_member(user2)
    assert message.is_from(user1)

# 测试场景2: User ↔ Agent
async def test_user_to_agent_conversation():
    user = Actor.from_user(user_id)
    agent = Actor.from_agent(agent_id)
    conversation = Conversation.create_direct(user, agent)
    message = Message.create(conversation.id, user, "Hello Hans!")

    assert conversation.is_direct()
    assert conversation.has_member(user)
    assert conversation.has_member(agent)

# 测试场景3: Agent ↔ Agent
async def test_agent_to_agent_conversation():
    agent1 = Actor.from_agent(agent1_id)
    agent2 = Actor.from_agent(agent2_id)
    conversation = Conversation.create_direct(agent1, agent2)
    message = Message.create(conversation.id, agent1, "Hello Alice!")

    assert conversation.is_direct()
    assert message.sender.is_agent()

# 测试场景4: 群聊
async def test_group_conversation():
    user = Actor.from_user(user_id)
    agent1 = Actor.from_agent(agent1_id)
    agent2 = Actor.from_agent(agent2_id)
    conversation = Conversation.create_group(
        "Study Group",
        [user, agent1, agent2]
    )

    assert conversation.is_group()
    assert len(conversation.members) == 3
    assert conversation.has_member(user)
    assert conversation.has_member(agent1)
    assert conversation.has_member(agent2)
```

## ✅ 验收标准

- [ ] Conversation、Message实体设计完成
- [ ] 数据库表创建成功，约束正确
- [ ] 仓储接口和实现完成
- [ ] 数据库迁移脚本可正常执行
- [ ] 支持User ↔ User通信
- [ ] 支持User ↔ Agent通信
- [ ] 支持Agent ↔ Agent通信
- [ ] 支持群聊功能
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 代码符合编码规范
- [ ] 与迭代6的Actor模型保持一致

## 🔧 技术要点

### 1. 双层抽象架构的优势

**领域层使用Actor，数据库层使用Participant**：
- 应用层代码简洁，使用Actor值对象
- 数据库层通过外键保证完整性
- 仓储层自动转换，对应用层透明

### 2. Participant自动管理

仓储层的`find_or_create`模式：
```python
async def find_or_create(self, actor: Actor) -> Participant:
    participant = await self.find_by_actor(actor)
    if not participant:
        participant = Participant.from_actor(actor)
        await self.save(participant)
    return participant
```

### 3. Direct会话去重

**数据库级约束**（防止并发竞态）：
- 使用唯一索引约束两个participant_id的组合
- 应用层先查询，数据库层保证幂等

**应用层查询**：
```python
existing = await conversation_repo.find_direct_conversation(actor1, actor2)
if existing and existing.status == ConversationStatus.ACTIVE:
    return ConversationDTO.from_entity(existing)
```

### 4. 会话类型

- **DIRECT**: 一对一会话（User ↔ User, User ↔ Agent, Agent ↔ Agent）
- **GROUP**: 群聊（多个参与者）

在conversations表中维护message_count字段：
```sql
-- 触发器：新增消息时自动+1
CREATE OR REPLACE FUNCTION increment_message_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET message_count = message_count + 1,
        last_message_at = NEW.created_at,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_increment_message_count
AFTER INSERT ON messages
FOR EACH ROW
EXECUTE FUNCTION increment_message_count();
```

### 5. 已读状态

在conversation_members表中记录last_read_at：
```python
# 计算未读消息数
async def get_unread_count(conversation_id: UUID, actor: Actor) -> int:
    member = await get_conversation_member(conversation_id, actor)
    if not member.last_read_at:
        return await count_messages(conversation_id)
    return await count_messages_after(conversation_id, member.last_read_at)
```

### 6. 外键验证

数据库层面通过外键约束自动验证：
- conversation_members.participant_id → participants.id
- messages.sender_id → participants.id
- 无需应用层手动验证Actor存在性

## 🔜 下一步

完成迭代7后，进入**迭代8: 消息系统-基础API**

## 📊 预期成果

完成本迭代后，系统将具备：
- ✅ 统一的Actor值对象模型
- ✅ 支持多种通信类型的数据模型
- ✅ Participant中间表保证数据完整性
- ✅ Direct会话数据库级去重约束
- ✅ 仓储接口和实现
- ✅ 完整的测试覆盖
- ✅ 与迭代6保持架构完全一致

---

**创建日期**: 2026-03-16
**修订日期**: 2026-03-16
**修订原因**: 采用双层抽象架构（Actor + Participant），与迭代6保持一致，添加Direct会话去重约束
