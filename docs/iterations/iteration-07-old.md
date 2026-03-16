# 迭代7: 消息系统-数据模型

> 设计和实现会话(Conversation)和消息(Message)的数据模型

## 📋 迭代信息

- **迭代编号**: 7
- **预计时间**: 1天
- **当前状态**: 🟡 计划中
- **依赖迭代**: 迭代6 ✅
- **开始日期**: 待定

## 🎯 迭代目标

设计和实现消息系统的核心数据模型，包括会话(Conversation)和消息(Message)实体，为后续的消息API和实时通信打下基础。

## 📝 任务清单

### 1. Conversation领域层

**任务**:
- [ ] 创建ConversationId值对象
- [ ] 创建Conversation实体
- [ ] 创建ConversationRepository接口
- [ ] 创建ConversationStatus枚举

**交付物**:
- `src/domain/messaging/value_objects/conversation_id.py`
- `src/domain/messaging/entities/conversation.py`
- `src/domain/messaging/repositories/conversation_repository.py`
- `src/domain/messaging/enums/conversation_status.py`

**设计要点**:
```python
# ConversationStatus枚举
class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

# Conversation实体
class Conversation:
    """会话实体。"""
    id: UUID
    user_id: UUID
    agent_id: UUID  # 关联到agents表
    title: Optional[str]  # 会话标题
    status: ConversationStatus
    message_count: int
    last_message_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
```

### 2. Message领域层

**任务**:
- [ ] 创建MessageId值对象
- [ ] 创建Message实体
- [ ] 创建MessageRepository接口
- [ ] 创建MessageRole枚举
- [ ] 创建MessageType枚举

**交付物**:
- `src/domain/messaging/value_objects/message_id.py`
- `src/domain/messaging/entities/message.py`
- `src/domain/messaging/repositories/message_repository.py`
- `src/domain/messaging/enums/message_role.py`
- `src/domain/messaging/enums/message_type.py`

**设计要点**:
```python
# MessageRole枚举
class MessageRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"

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
    role: MessageRole
    message_type: MessageType
    content: str
    metadata: Optional[dict]  # 额外信息（如文件URL、图片URL等）
    created_at: datetime
```

### 3. 数据库模型

**任务**:
- [ ] 创建ConversationModel
- [ ] 创建MessageModel
- [ ] 创建数据库迁移脚本

**交付物**:
- `src/infrastructure/persistence/models/conversation_model.py`
- `src/infrastructure/persistence/models/message_model.py`
- `migrations/versions/xxx_create_conversations_messages_tables.py`

**数据库表设计**:
```sql
-- conversations表
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    title VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- messages表
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text',
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_agent_id ON conversations(agent_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_last_message_at ON conversations(last_message_at DESC);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

### 4. 仓储实现

**任务**:
- [ ] 创建PostgresConversationRepository
- [ ] 创建PostgresMessageRepository
- [ ] 实现实体与模型的转换方法

**交付物**:
- `src/infrastructure/persistence/repositories/postgres_conversation_repository.py`
- `src/infrastructure/persistence/repositories/postgres_message_repository.py`

**仓储方法**:
```python
# ConversationRepository
class ConversationRepository(ABC):
    async def save(conversation: Conversation) -> Conversation
    async def find_by_id(conversation_id: UUID) -> Optional[Conversation]
    async def find_by_user_id(user_id: UUID, limit: int, offset: int) -> List[Conversation]
    async def find_by_user_and_agent(user_id: UUID, agent_id: UUID) -> List[Conversation]
    async def update(conversation: Conversation) -> Conversation
    async def delete(conversation_id: UUID) -> None
    async def count_by_user_id(user_id: UUID) -> int

# MessageRepository
class MessageRepository(ABC):
    async def save(message: Message) -> Message
    async def find_by_id(message_id: UUID) -> Optional[Message]
    async def find_by_conversation_id(conversation_id: UUID, limit: int, offset: int) -> List[Message]
    async def count_by_conversation_id(conversation_id: UUID) -> int
    async def delete(message_id: UUID) -> None
```

### 5. 测试

**任务**:
- [ ] 编写Conversation实体单元测试
- [ ] 编写Message实体单元测试
- [ ] 编写仓储集成测试
- [ ] 测试数据库迁移

**交付物**:
- `tests/unit/domain/messaging/test_conversation_entity.py`
- `tests/unit/domain/messaging/test_message_entity.py`
- `tests/integration/test_conversation_repository.py`
- `tests/integration/test_message_repository.py`

## ✅ 验收标准

- [ ] Conversation和Message实体设计完成
- [ ] 数据库表创建成功
- [ ] 仓储接口和实现完成
- [ ] 数据库迁移脚本可正常执行
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 代码符合编码规范

## 🔧 技术要点

### 1. 会话与消息的关系

- 一个会话(Conversation)包含多条消息(Message)
- 使用外键关联：messages.conversation_id → conversations.id
- 级联删除：删除会话时自动删除所有消息

### 2. 消息计数优化

在conversations表中维护message_count字段：
- 新增消息时自动+1
- 删除消息时自动-1
- 避免每次都COUNT查询

### 3. 消息排序

- 使用created_at字段排序
- 创建索引优化查询性能
- 支持分页查询

### 4. 元数据存储

使用JSONB字段存储消息的额外信息：
```python
metadata = {
    "file_url": "https://...",
    "file_name": "document.pdf",
    "file_size": 1024000,
    "image_url": "https://...",
    "image_width": 800,
    "image_height": 600
}
```

### 5. 会话状态管理

- ACTIVE: 活跃会话
- ARCHIVED: 已归档（用户不再使用但保留）
- DELETED: 已删除（软删除，可恢复）

## 🔜 下一步

完成迭代7后，进入**迭代8: 消息系统-基础API**

## 📊 预期成果

完成本迭代后，系统将具备：
- ✅ 完整的消息数据模型
- ✅ 会话和消息的数据库表
- ✅ 仓储接口和实现
- ✅ 完整的测试覆盖

---

**创建日期**: 2026-03-16
