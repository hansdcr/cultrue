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

**核心思想**：使用Actor值对象统一抽象User和Agent，通过多态引用实现任意类型间的通信。

### 设计优势

- ✅ 支持User ↔ User通信
- ✅ 支持User ↔ Agent通信
- ✅ 支持Agent ↔ Agent通信
- ✅ 支持群聊（多人/多Agent）
- ✅ 无需中间表，数据模型简洁
- ✅ 符合DDD设计原则
- ✅ 与迭代6的Actor模型保持一致

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

-- conversation_members表（会话成员，使用多态引用）
CREATE TABLE conversation_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    actor_type VARCHAR(20) NOT NULL,  -- 'user' or 'agent'
    actor_id UUID NOT NULL,           -- user_id or agent_id
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_read_at TIMESTAMP WITH TIME ZONE,
    is_muted BOOLEAN DEFAULT FALSE,
    UNIQUE(conversation_id, actor_type, actor_id),
    CONSTRAINT check_actor_type CHECK (actor_type IN ('user', 'agent'))
);

-- messages表（消息，使用多态引用）
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL,  -- 'user' or 'agent'
    sender_id UUID NOT NULL,           -- user_id or agent_id
    message_type VARCHAR(20) DEFAULT 'text',
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_sender_type CHECK (sender_type IN ('user', 'agent'))
);

-- 索引
CREATE INDEX idx_conversations_type ON conversations(conversation_type);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_last_message_at ON conversations(last_message_at DESC);
CREATE INDEX idx_conversation_members_conversation_id ON conversation_members(conversation_id);
CREATE INDEX idx_conversation_members_actor ON conversation_members(actor_type, actor_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_sender ON messages(sender_type, sender_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

**设计说明**:
- **无需participants表**: 直接使用(actor_type, actor_id)多态引用
- **外键验证**: 通过应用层逻辑确保actor_id有效（查询users或agents表）
- **复合索引**: 在(actor_type, actor_id)上建立索引以优化查询性能

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

**Actor序列化示例**:
```python
# 实体 → 模型
def conversation_to_model(conversation: Conversation) -> ConversationModel:
    model = ConversationModel(
        id=conversation.id,
        conversation_type=conversation.conversation_type.value,
        title=conversation.title,
        status=conversation.status.value,
        message_count=conversation.message_count,
        last_message_at=conversation.last_message_at,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )
    # 成员单独保存到conversation_members表
    return model

# 模型 → 实体
async def model_to_conversation(
    model: ConversationModel,
    members: List[ConversationMemberModel]
) -> Conversation:
    actors = [
        Actor(
            actor_type=ActorType(m.actor_type),
            actor_id=m.actor_id
        )
        for m in members
    ]
    return Conversation(
        id=model.id,
        conversation_type=ConversationType(model.conversation_type),
        title=model.title,
        status=ConversationStatus(model.status),
        members=actors,
        message_count=model.message_count,
        last_message_at=model.last_message_at,
        created_at=model.created_at,
        updated_at=model.updated_at
    )
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

### 1. Actor值对象的优势

**简洁性**:
- 无需中间表（participants）
- 直接使用多态引用
- 减少JOIN查询

**一致性**:
- 与迭代6的Contact系统保持一致
- 统一的Actor抽象
- 易于理解和维护

### 2. 多态引用

使用(actor_type, actor_id)组合：
```sql
-- 查询用户的所有会话
SELECT c.* FROM conversations c
JOIN conversation_members cm ON c.id = cm.conversation_id
WHERE cm.actor_type = 'user' AND cm.actor_id = ?

-- 查询Agent的所有会话
SELECT c.* FROM conversations c
JOIN conversation_members cm ON c.id = cm.conversation_id
WHERE cm.actor_type = 'agent' AND cm.actor_id = ?
```

### 3. 会话类型

- **DIRECT**: 一对一会话（User ↔ User, User ↔ Agent, Agent ↔ Agent）
- **GROUP**: 群聊（多个参与者）

### 4. 消息计数优化

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

由于使用多态引用，数据库层面无法建立外键约束，需要在应用层验证：
```python
async def validate_actor(actor: Actor) -> bool:
    """验证Actor是否存在。"""
    if actor.is_user():
        user = await user_repository.find_by_id(actor.actor_id)
        return user is not None
    else:
        agent = await agent_repository.find_by_id(actor.actor_id)
        return agent is not None
```

## 🔜 下一步

完成迭代7后，进入**迭代8: 消息系统-基础API**

## 📊 预期成果

完成本迭代后，系统将具备：
- ✅ 统一的Actor值对象模型
- ✅ 支持多种通信类型的数据模型
- ✅ 简洁的会话和消息数据库表
- ✅ 仓储接口和实现
- ✅ 完整的测试覆盖
- ✅ 与迭代6保持架构一致性

---

**创建日期**: 2026-03-16
**修订日期**: 2026-03-16
**修订原因**: 采用Solution C的Actor模型，移除Participant中间层
