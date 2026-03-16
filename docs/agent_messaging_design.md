# Agent和消息系统设计方案

> 支持User ↔ User、User ↔ Agent、Agent ↔ Agent以及群聊的统一消息系统

## 📋 文档信息

- **创建日期**: 2026-03-16
- **版本**: v2.0（改进版）
- **状态**: 已规划

## 🎯 设计目标

实现一个统一的消息系统，支持以下通信场景：
- ✅ User ↔ User（人与人）
- ✅ User ↔ Agent（人与AI）
- ✅ Agent ↔ Agent（AI与AI）
- ✅ 群聊（多人/多Agent）

## 💡 核心设计理念

**将Agent视为一种特殊的User**，通过统一的Participant（参与者）抽象，实现任意类型间的通信。

### 设计优势

1. **统一抽象**：User和Agent都是Participant，简化数据模型
2. **灵活扩展**：未来可轻松添加其他类型参与者（Bot、System等）
3. **数据一致性**：使用外键约束确保数据完整性
4. **易于理解**：符合直觉的领域模型

## 🏗️ 架构设计

### 核心实体关系

```
┌─────────────┐         ┌─────────────┐
│    User     │         │    Agent    │
└──────┬──────┘         └──────┬──────┘
       │                       │
       │  1:1                  │  1:1
       │                       │
       ▼                       ▼
┌──────────────────────────────────┐
│         Participant              │
│  ┌────────────────────────────┐ │
│  │ participant_type: enum     │ │
│  │ user_id: UUID (nullable)   │ │
│  │ agent_id: UUID (nullable)  │ │
│  │ display_name: string       │ │
│  │ avatar_url: string         │ │
│  └────────────────────────────┘ │
└──────────────┬───────────────────┘
               │
               │  M:N
               │
               ▼
┌──────────────────────────────────┐
│        Conversation              │
│  ┌────────────────────────────┐ │
│  │ conversation_type: enum    │ │
│  │ title: string              │ │
│  │ status: enum               │ │
│  │ message_count: int         │ │
│  │ last_message_at: datetime  │ │
│  └────────────────────────────┘ │
└──────────────┬───────────────────┘
               │
               │  1:N
               │
               ▼
┌──────────────────────────────────┐
│           Message                │
│  ┌────────────────────────────┐ │
│  │ sender_id: UUID            │ │
│  │ message_type: enum         │ │
│  │ content: text              │ │
│  │ metadata: jsonb            │ │
│  │ created_at: datetime       │ │
│  └────────────────────────────┘ │
└──────────────────────────────────┘
```

### 数据库表结构

#### 1. participants表（统一参与者）

```sql
CREATE TABLE participants (
    id UUID PRIMARY KEY,
    participant_type VARCHAR(20) NOT NULL,  -- 'user' or 'agent'
    user_id UUID REFERENCES users(id),
    agent_id UUID REFERENCES agents(id),
    display_name VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE,

    -- 约束：确保类型与ID匹配
    CONSTRAINT check_participant_type CHECK (
        (participant_type = 'user' AND user_id IS NOT NULL AND agent_id IS NULL) OR
        (participant_type = 'agent' AND agent_id IS NOT NULL AND user_id IS NULL)
    ),

    -- 唯一约束：每个User/Agent只有一个Participant
    CONSTRAINT unique_user_participant UNIQUE (user_id),
    CONSTRAINT unique_agent_participant UNIQUE (agent_id)
);
```

**设计要点**：
- `participant_type`：区分User和Agent
- `user_id`和`agent_id`：互斥，只能有一个非空
- 约束确保数据一致性
- 每个User/Agent只创建一次Participant

#### 2. conversations表（会话）

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    conversation_type VARCHAR(20) DEFAULT 'direct',  -- 'direct' or 'group'
    title VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

**设计要点**：
- `conversation_type`：区分一对一和群聊
- `message_count`：冗余字段，优化查询性能
- `last_message_at`：用于排序，显示最近活跃的会话

#### 3. conversation_participants表（会话参与者）

```sql
CREATE TABLE conversation_participants (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    participant_id UUID REFERENCES participants(id) ON DELETE CASCADE,
    joined_at TIMESTAMP WITH TIME ZONE,
    last_read_at TIMESTAMP WITH TIME ZONE,
    is_muted BOOLEAN DEFAULT FALSE,

    UNIQUE(conversation_id, participant_id)
);
```

**设计要点**：
- 多对多关系：一个会话有多个参与者，一个参与者参与多个会话
- `last_read_at`：记录已读位置，计算未读消息数
- `is_muted`：静音功能

#### 4. messages表（消息）

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES participants(id) ON DELETE CASCADE,
    message_type VARCHAR(20) DEFAULT 'text',
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE
);
```

**设计要点**：
- `sender_id`：指向Participant，统一处理User和Agent
- `message_type`：支持文本、图片、文件等多种类型
- `metadata`：JSONB字段存储额外信息

## 🔄 通信场景实现

### 场景1: User ↔ User（人与人）

```python
# 1. 创建Participant
user1_participant = await participant_repo.find_or_create_from_user(
    user1_id, "Alice", "avatar1.jpg"
)
user2_participant = await participant_repo.find_or_create_from_user(
    user2_id, "Bob", "avatar2.jpg"
)

# 2. 创建会话
conversation = Conversation.create_direct(
    user1_participant.id, user2_participant.id
)
await conversation_repo.save(conversation)

# 3. 发送消息
message = Message.create(
    conversation.id, user1_participant.id, "Hello Bob!"
)
await message_repo.save(message)
```

### 场景2: User ↔ Agent（人与AI）

```python
# 1. 创建Participant
user_participant = await participant_repo.find_or_create_from_user(
    user_id, "Alice", "avatar.jpg"
)
agent_participant = await participant_repo.find_or_create_from_agent(
    agent_id, "Hans", "hans.jpg"
)

# 2. 创建会话
conversation = Conversation.create_direct(
    user_participant.id, agent_participant.id
)
await conversation_repo.save(conversation)

# 3. User发送消息
user_message = Message.create(
    conversation.id, user_participant.id, "Hello Hans!"
)
await message_repo.save(user_message)

# 4. Agent回复消息
agent_message = Message.create(
    conversation.id, agent_participant.id, "Hello Alice! How can I help you?"
)
await message_repo.save(agent_message)
```

### 场景3: Agent ↔ Agent（AI与AI）

```python
# 1. 创建Participant
agent1_participant = await participant_repo.find_or_create_from_agent(
    agent1_id, "Hans", "hans.jpg"
)
agent2_participant = await participant_repo.find_or_create_from_agent(
    agent2_id, "Alice", "alice.jpg"
)

# 2. 创建会话
conversation = Conversation.create_direct(
    agent1_participant.id, agent2_participant.id
)
await conversation_repo.save(conversation)

# 3. Agent间对话
message = Message.create(
    conversation.id, agent1_participant.id, "Hello Alice, let's discuss..."
)
await message_repo.save(message)
```

### 场景4: 群聊（多人/多Agent）

```python
# 1. 创建Participant
user_participant = await participant_repo.find_or_create_from_user(
    user_id, "Alice", "avatar.jpg"
)
agent1_participant = await participant_repo.find_or_create_from_agent(
    agent1_id, "Hans", "hans.jpg"
)
agent2_participant = await participant_repo.find_or_create_from_agent(
    agent2_id, "Bob", "bob.jpg"
)

# 2. 创建群聊
conversation = Conversation.create_group(
    "Study Group",
    [user_participant.id, agent1_participant.id, agent2_participant.id]
)
await conversation_repo.save(conversation)

# 3. 任意参与者发送消息
message = Message.create(
    conversation.id, user_participant.id, "Let's start our discussion!"
)
await message_repo.save(message)
```

## 📊 API设计

### 会话API

```
POST   /api/conversations                    # 创建会话
GET    /api/conversations                    # 获取会话列表
GET    /api/conversations/{id}               # 获取会话详情
POST   /api/conversations/{id}/participants  # 添加参与者（群聊）
DELETE /api/conversations/{id}/participants/{participant_id}  # 移除参与者
PUT    /api/conversations/{id}/archive       # 归档会话
DELETE /api/conversations/{id}               # 删除会话
```

### 消息API

```
POST   /api/conversations/{id}/messages      # 发送消息
GET    /api/conversations/{id}/messages      # 获取消息列表
GET    /api/messages/{id}                    # 获取消息详情
DELETE /api/messages/{id}                    # 删除消息
```

## 🔐 权限控制

### 会话权限

- ✅ 只有参与者可以查看会话
- ✅ 只有参与者可以发送消息
- ✅ 只有创建者可以添加/移除参与者（群聊）
- ✅ 只有参与者可以归档/删除会话

### 消息权限

- ✅ 只有发送者可以删除消息
- ✅ 只有会话参与者可以查看消息

## 📈 性能优化

### 1. 索引优化

```sql
-- Participant索引
CREATE INDEX idx_participants_type ON participants(participant_type);
CREATE INDEX idx_participants_user_id ON participants(user_id);
CREATE INDEX idx_participants_agent_id ON participants(agent_id);

-- Conversation索引
CREATE INDEX idx_conversations_last_message_at ON conversations(last_message_at DESC);

-- Message索引
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

### 2. 消息计数缓存

在conversations表中维护message_count字段，避免每次COUNT查询。

### 3. 分页查询

使用LIMIT和OFFSET实现分页：
```python
messages = await message_repo.find_by_conversation_id(
    conversation_id, limit=50, offset=0
)
```

### 4. 未读消息优化

在conversation_participants表中记录last_read_at：
```sql
SELECT COUNT(*) FROM messages
WHERE conversation_id = ? AND created_at > last_read_at
```

## 🧪 测试策略

### 单元测试

- Participant实体测试
- Conversation实体测试
- Message实体测试
- 仓储接口测试

### 集成测试

- User ↔ User通信测试
- User ↔ Agent通信测试
- Agent ↔ Agent通信测试
- 群聊功能测试
- 权限控制测试

### 端到端测试

- 完整的会话创建和消息发送流程
- 多种通信场景组合测试

## 🔜 迭代计划

### 迭代6: Agent管理（1-2天）

- ✅ Agent领域层实现
- ✅ Agent应用层实现
- ✅ Agent基础设施层实现
- ✅ Agent REST API
- ✅ 用户与Agent关联
- ✅ 默认Agent初始化

### 迭代7: 消息系统-数据模型（1-2天）

- ✅ Participant领域层实现
- ✅ Conversation领域层实现
- ✅ Message领域层实现
- ✅ 数据库表创建
- ✅ 仓储实现
- ✅ 单元测试

### 迭代8: 消息系统-基础API（1-2天）

- ✅ Conversation应用层实现
- ✅ Message应用层实现
- ✅ REST API实现
- ✅ 权限控制
- ✅ 集成测试

**总计**: 3-6天完成Agent和消息系统

## 📝 总结

### 设计优势

1. **统一抽象**：User和Agent统一为Participant，简化模型
2. **灵活扩展**：支持任意类型间通信，易于添加新类型
3. **数据一致性**：外键约束确保数据完整性
4. **性能优化**：合理的索引和缓存策略
5. **符合DDD**：清晰的领域模型和分层架构

### 与原设计对比

| 特性 | 原设计 | 改进设计 |
|------|--------|---------|
| User ↔ Agent | ✅ | ✅ |
| User ↔ User | ❌ | ✅ |
| Agent ↔ Agent | ❌ | ✅ |
| 群聊 | ❌ | ✅ |
| 扩展性 | 低 | 高 |
| 数据一致性 | 中 | 高 |

### 下一步

完成Agent和消息系统后，进入**里程碑3: 实时通信**，实现WebSocket实时消息推送。

---

**创建日期**: 2026-03-16
**版本**: v2.0
**状态**: 已规划
