# 迭代7: 消息系统-数据模型（改进版）

> 设计和实现支持多类型参与者的消息系统数据模型

## 📋 迭代信息

- **迭代编号**: 7
- **预计时间**: 1-2天
- **当前状态**: 🟡 计划中
- **依赖迭代**: 迭代6 ✅
- **开始日期**: 待定

## 🎯 迭代目标

设计和实现支持**User ↔ User**、**User ↔ Agent**、**Agent ↔ Agent**以及**群聊**的统一消息系统数据模型。

## 💡 设计理念

**核心思想**：将User和Agent统一抽象为Participant（参与者），实现任意类型间的通信。

### 设计优势

- ✅ 支持User ↔ User通信
- ✅ 支持User ↔ Agent通信
- ✅ 支持Agent ↔ Agent通信
- ✅ 支持群聊（多人/多Agent）
- ✅ 数据模型统一，易于扩展
- ✅ 符合DDD设计原则

## 📝 任务清单

### 1. Participant领域层

**任务**:
- [ ] 创建ParticipantType枚举
- [ ] 创建ParticipantId值对象
- [ ] 创建Participant实体
- [ ] 创建ParticipantRepository接口

**交付物**:
- `src/domain/messaging/enums/participant_type.py`
- `src/domain/messaging/value_objects/participant_id.py`
- `src/domain/messaging/entities/participant.py`
- `src/domain/messaging/repositories/participant_repository.py`

**设计要点**:
```python
# ParticipantType枚举
class ParticipantType(str, Enum):
    USER = "user"
    AGENT = "agent"

# Participant实体
class Participant:
    """参与者实体（统一User和Agent）。"""
    id: UUID
    participant_type: ParticipantType
    user_id: Optional[UUID]  # 如果是user类型
    agent_id: Optional[UUID]  # 如果是agent类型
    display_name: str
    avatar_url: Optional[str]
    created_at: datetime

    @classmethod
    def from_user(cls, user_id: UUID, display_name: str, avatar_url: Optional[str]) -> "Participant":
        """从User创建Participant。"""
        pass

    @classmethod
    def from_agent(cls, agent_id: UUID, display_name: str, avatar_url: Optional[str]) -> "Participant":
        """从Agent创建Participant。"""
        pass

    def is_user(self) -> bool:
        return self.participant_type == ParticipantType.USER

    def is_agent(self) -> bool:
        return self.participant_type == ParticipantType.AGENT
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
class Conversation:
    """会话实体。"""
    id: UUID
    conversation_type: ConversationType
    title: Optional[str]
    status: ConversationStatus
    participants: List[UUID]  # participant_ids
    message_count: int
    last_message_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    def add_participant(self, participant_id: UUID) -> None:
        """添加参与者。"""
        pass

    def remove_participant(self, participant_id: UUID) -> None:
        """移除参与者。"""
        pass

    def is_direct(self) -> bool:
        return self.conversation_type == ConversationType.DIRECT

    def is_group(self) -> bool:
        return self.conversation_type == ConversationType.GROUP
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
class Message:
    """消息实体。"""
    id: UUID
    conversation_id: UUID
    sender_id: UUID  # participant_id
    message_type: MessageType
    content: str
    metadata: Optional[dict]
    created_at: datetime

    def is_from_user(self, participant: Participant) -> bool:
        """判断消息是否来自指定参与者。"""
        return self.sender_id == participant.id
```

### 4. 数据库模型

**任务**:
- [ ] 创建ParticipantModel
- [ ] 创建ConversationModel
- [ ] 创建ConversationParticipantModel（关联表）
- [ ] 创建MessageModel
- [ ] 创建数据库迁移脚本

**交付物**:
- `src/infrastructure/persistence/models/participant_model.py`
- `src/infrastructure/persistence/models/conversation_model.py`
- `src/infrastructure/persistence/models/conversation_participant_model.py`
- `src/infrastructure/persistence/models/message_model.py`
- `migrations/versions/xxx_create_messaging_tables.py`

**数据库表设计**:
```sql
-- participants表（统一的参与者）
CREATE TABLE participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    participant_type VARCHAR(20) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    display_name VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_participant_type CHECK (
        (participant_type = 'user' AND user_id IS NOT NULL AND agent_id IS NULL) OR
        (participant_type = 'agent' AND agent_id IS NOT NULL AND user_id IS NULL)
    ),
    CONSTRAINT unique_user_participant UNIQUE (user_id),
    CONSTRAINT unique_agent_participant UNIQUE (agent_id)
);

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

-- conversation_participants表（会话参与者，多对多）
CREATE TABLE conversation_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    participant_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_read_at TIMESTAMP WITH TIME ZONE,
    is_muted BOOLEAN DEFAULT FALSE,
    UNIQUE(conversation_id, participant_id)
);

-- messages表（消息）
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    message_type VARCHAR(20) DEFAULT 'text',
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_participants_type ON participants(participant_type);
CREATE INDEX idx_participants_user_id ON participants(user_id);
CREATE INDEX idx_participants_agent_id ON participants(agent_id);
CREATE INDEX idx_conversations_type ON conversations(conversation_type);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_last_message_at ON conversations(last_message_at DESC);
CREATE INDEX idx_conversation_participants_conversation_id ON conversation_participants(conversation_id);
CREATE INDEX idx_conversation_participants_participant_id ON conversation_participants(participant_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_sender_id ON messages(sender_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

### 5. 仓储实现

**任务**:
- [ ] 创建PostgresParticipantRepository
- [ ] 创建PostgresConversationRepository
- [ ] 创建PostgresMessageRepository
- [ ] 实现实体与模型的转换方法

**交付物**:
- `src/infrastructure/persistence/repositories/postgres_participant_repository.py`
- `src/infrastructure/persistence/repositories/postgres_conversation_repository.py`
- `src/infrastructure/persistence/repositories/postgres_message_repository.py`

**仓储方法**:
```python
# ParticipantRepository
class ParticipantRepository(ABC):
    async def save(participant: Participant) -> Participant
    async def find_by_id(participant_id: UUID) -> Optional[Participant]
    async def find_by_user_id(user_id: UUID) -> Optional[Participant]
    async def find_by_agent_id(agent_id: UUID) -> Optional[Participant]
    async def find_or_create_from_user(user_id: UUID, display_name: str, avatar_url: Optional[str]) -> Participant
    async def find_or_create_from_agent(agent_id: UUID, display_name: str, avatar_url: Optional[str]) -> Participant

# ConversationRepository
class ConversationRepository(ABC):
    async def save(conversation: Conversation) -> Conversation
    async def find_by_id(conversation_id: UUID) -> Optional[Conversation]
    async def find_by_participant_id(participant_id: UUID, limit: int, offset: int) -> List[Conversation]
    async def find_direct_conversation(participant1_id: UUID, participant2_id: UUID) -> Optional[Conversation]
    async def add_participant(conversation_id: UUID, participant_id: UUID) -> None
    async def remove_participant(conversation_id: UUID, participant_id: UUID) -> None
    async def update(conversation: Conversation) -> Conversation
    async def delete(conversation_id: UUID) -> None

# MessageRepository
class MessageRepository(ABC):
    async def save(message: Message) -> Message
    async def find_by_id(message_id: UUID) -> Optional[Message]
    async def find_by_conversation_id(conversation_id: UUID, limit: int, offset: int) -> List[Message]
    async def count_by_conversation_id(conversation_id: UUID) -> int
    async def delete(message_id: UUID) -> None
```

### 6. 测试

**任务**:
- [ ] 编写Participant实体单元测试
- [ ] 编写Conversation实体单元测试
- [ ] 编写Message实体单元测试
- [ ] 编写仓储集成测试
- [ ] 测试数据库迁移
- [ ] 测试多种通信场景

**交付物**:
- `tests/unit/domain/messaging/test_participant_entity.py`
- `tests/unit/domain/messaging/test_conversation_entity.py`
- `tests/unit/domain/messaging/test_message_entity.py`
- `tests/integration/test_participant_repository.py`
- `tests/integration/test_conversation_repository.py`
- `tests/integration/test_message_repository.py`

**测试场景**:
```python
# 测试场景1: User ↔ User
def test_user_to_user_conversation():
    user1_participant = Participant.from_user(user1_id, "Alice", "avatar1.jpg")
    user2_participant = Participant.from_user(user2_id, "Bob", "avatar2.jpg")
    conversation = Conversation.create_direct(user1_participant.id, user2_participant.id)
    message = Message.create(conversation.id, user1_participant.id, "Hello Bob!")

# 测试场景2: User ↔ Agent
def test_user_to_agent_conversation():
    user_participant = Participant.from_user(user_id, "Alice", "avatar.jpg")
    agent_participant = Participant.from_agent(agent_id, "Hans", "hans.jpg")
    conversation = Conversation.create_direct(user_participant.id, agent_participant.id)
    message = Message.create(conversation.id, user_participant.id, "Hello Hans!")

# 测试场景3: Agent ↔ Agent
def test_agent_to_agent_conversation():
    agent1_participant = Participant.from_agent(agent1_id, "Hans", "hans.jpg")
    agent2_participant = Participant.from_agent(agent2_id, "Alice", "alice.jpg")
    conversation = Conversation.create_direct(agent1_participant.id, agent2_participant.id)
    message = Message.create(conversation.id, agent1_participant.id, "Hello Alice!")

# 测试场景4: 群聊
def test_group_conversation():
    user_participant = Participant.from_user(user_id, "Alice", "avatar.jpg")
    agent1_participant = Participant.from_agent(agent1_id, "Hans", "hans.jpg")
    agent2_participant = Participant.from_agent(agent2_id, "Bob", "bob.jpg")
    conversation = Conversation.create_group("Study Group", [user_participant.id, agent1_participant.id, agent2_participant.id])
```

## ✅ 验收标准

- [ ] Participant、Conversation、Message实体设计完成
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

## 🔧 技术要点

### 1. 统一参与者模型

**优势**:
- 数据一致性：使用外键约束确保参与者有效
- 扩展性强：未来可添加其他类型参与者（如Bot、System）
- 查询简单：统一的participant_id便于查询

**约束**:
```sql
CONSTRAINT check_participant_type CHECK (
    (participant_type = 'user' AND user_id IS NOT NULL AND agent_id IS NULL) OR
    (participant_type = 'agent' AND agent_id IS NOT NULL AND user_id IS NULL)
)
```

### 2. 会话类型

- **DIRECT**: 一对一会话（User ↔ User, User ↔ Agent, Agent ↔ Agent）
- **GROUP**: 群聊（多个参与者）

### 3. 参与者自动创建

当User或Agent首次参与会话时，自动创建对应的Participant记录：
```python
participant = await participant_repo.find_or_create_from_user(user_id, user.full_name, user.avatar_url)
```

### 4. 消息计数优化

在conversations表中维护message_count字段：
- 新增消息时触发器自动+1
- 删除消息时触发器自动-1

### 5. 已读状态

在conversation_participants表中记录last_read_at：
- 用户打开会话时更新
- 计算未读消息数：COUNT(messages WHERE created_at > last_read_at)

## 🔜 下一步

完成迭代7后，进入**迭代8: 消息系统-基础API**

## 📊 预期成果

完成本迭代后，系统将具备：
- ✅ 统一的参与者模型
- ✅ 支持多种通信类型的数据模型
- ✅ 完整的会话和消息数据库表
- ✅ 仓储接口和实现
- ✅ 完整的测试覆盖

---

**创建日期**: 2026-03-16
**修订日期**: 2026-03-16
**修订原因**: 改进设计以支持多类型参与者通信
