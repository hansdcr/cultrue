# 消息系统设计（Messaging System Design）

## 需求概述

系统需要支持以下通信场景：
1. ✅ **User ↔ User** - 人类之间的聊天
2. ✅ **User ↔ Agent** - 人类与AI智能体的聊天
3. ✅ **Agent ↔ Agent** - AI智能体之间的聊天
4. ✅ **Agent主动发起** - Agent可以主动给User或其他Agent发送消息

## 核心设计原则

1. **参与者抽象**：User和Agent都是"参与者"（Participant），使用统一的接口
2. **会话中心**：所有消息都属于某个会话（Conversation）
3. **实时推送**：使用WebSocket实现实时消息推送
4. **异步处理**：Agent的消息生成和发送使用异步任务队列

## 数据库设计

### conversations表（会话表）
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255),  -- 会话标题（可选，群聊时有用）
    type VARCHAR(20) NOT NULL,  -- 'direct'（单聊）, 'group'（群聊）
    created_by_type VARCHAR(10),  -- 'user' or 'agent'
    created_by_id UUID,  -- 创建者ID
    metadata JSONB,  -- 额外信息，如会话配置、标签等
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP  -- 最后一条消息时间，用于排序
);
CREATE INDEX idx_conversations_type ON conversations(type);
CREATE INDEX idx_conversations_last_message_at ON conversations(last_message_at DESC);
```

### conversation_participants表（会话参与者表）
```sql
CREATE TABLE conversation_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    participant_type VARCHAR(10) NOT NULL,  -- 'user' or 'agent'
    participant_id UUID NOT NULL,  -- 指向users.id或agents.id
    role VARCHAR(20) DEFAULT 'member',  -- 'member', 'admin'（群聊中可能有用）
    is_muted BOOLEAN DEFAULT FALSE,  -- 是否静音此会话
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_read_at TIMESTAMP,  -- 最后阅读时间，用于计算未读消息数
    left_at TIMESTAMP,  -- 离开会话的时间（可选）
    UNIQUE(conversation_id, participant_type, participant_id)
);
CREATE INDEX idx_conv_participants_conversation ON conversation_participants(conversation_id);
CREATE INDEX idx_conv_participants_participant ON conversation_participants(participant_type, participant_id);
```

### messages表（消息表）
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    sender_type VARCHAR(10) NOT NULL,  -- 'user' or 'agent'
    sender_id UUID NOT NULL,  -- 指向users.id或agents.id
    content TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text',  -- 'text', 'image', 'file', 'system', 'ai_generated'
    metadata JSONB,  -- 额外信息：文件URL、AI生成参数、引用消息等
    reply_to_message_id UUID REFERENCES messages(id),  -- 回复的消息ID
    is_deleted BOOLEAN DEFAULT FALSE,
    is_edited BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_messages_sender ON messages(sender_type, sender_id);
CREATE INDEX idx_messages_reply_to ON messages(reply_to_message_id);
```

### message_read_status表（消息已读状态）
```sql
CREATE TABLE message_read_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    reader_type VARCHAR(10) NOT NULL,  -- 'user' or 'agent'
    reader_id UUID NOT NULL,  -- 指向users.id或agents.id
    read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(message_id, reader_type, reader_id)
);
CREATE INDEX idx_message_read_status_message ON message_read_status(message_id);
CREATE INDEX idx_message_read_status_reader ON message_read_status(reader_type, reader_id);
```

### agent_triggers表（Agent触发器配置）
```sql
CREATE TABLE agent_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    trigger_type VARCHAR(50) NOT NULL,  -- 'scheduled', 'event_based', 'keyword', 'context_change'
    trigger_config JSONB NOT NULL,  -- 触发器配置：时间、关键词、事件类型等
    target_type VARCHAR(10),  -- 'user', 'agent', 'conversation'（目标类型）
    target_id UUID,  -- 目标ID
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_agent_triggers_agent ON agent_triggers(agent_id);
CREATE INDEX idx_agent_triggers_type ON agent_triggers(trigger_type);
```

## DDD架构设计

### Messaging领域（新增）

```
src/domain/messaging/
├── entities/
│   ├── conversation.py          # 会话实体
│   ├── message.py               # 消息实体
│   └── participant.py           # 参与者实体（抽象）
├── value_objects/
│   ├── conversation_id.py
│   ├── message_id.py
│   ├── participant_info.py      # 参与者信息（type + id）
│   └── message_content.py
├── repositories/
│   ├── conversation_repository.py    # 会话仓储接口
│   ├── message_repository.py         # 消息仓储接口
│   └── participant_repository.py     # 参与者仓储接口
└── services/
    ├── conversation_service.py       # 会话领域服务
    ├── message_service.py            # 消息领域服务
    └── participant_resolver.py       # 参与者解析服务

src/application/messaging/
├── commands/
│   ├── create_conversation_command.py
│   ├── send_message_command.py
│   ├── mark_as_read_command.py
│   └── add_participant_command.py
├── queries/
│   ├── get_conversations_query.py
│   ├── get_messages_query.py
│   ├── get_unread_count_query.py
│   └── search_conversations_query.py
└── dtos/
    ├── conversation_dto.py
    ├── message_dto.py
    └── participant_dto.py

src/infrastructure/messaging/
├── repositories/
│   ├── postgres_conversation_repository.py
│   ├── postgres_message_repository.py
│   └── postgres_participant_repository.py
├── websocket/
│   ├── connection_manager.py         # WebSocket连接管理
│   ├── message_broadcaster.py        # 消息广播器
│   └── event_handlers.py             # WebSocket事件处理
└── tasks/
    ├── agent_message_scheduler.py    # Agent消息调度器
    └── trigger_processor.py          # 触发器处理器

src/interfaces/api/
├── rest/
│   └── messaging.py                  # 消息REST API
├── websocket/
│   └── chat_ws.py                    # WebSocket端点
└── schemas/
    └── messaging_schema.py           # 消息相关Pydantic模型
```

## API设计

### REST API端点

#### 会话管理
- `GET /api/conversations` - 获取会话列表（支持筛选：type, participant）
- `GET /api/conversations/{conversation_id}` - 获取会话详情
- `POST /api/conversations` - 创建会话
  ```json
  {
    "type": "direct",  // or "group"
    "participants": [
      {"type": "user", "id": "uuid"},
      {"type": "agent", "id": "uuid"}
    ],
    "title": "可选标题"
  }
  ```
- `PUT /api/conversations/{conversation_id}` - 更新会话（标题、设置等）
- `DELETE /api/conversations/{conversation_id}` - 删除/归档会话
- `POST /api/conversations/{conversation_id}/participants` - 添加参与者（群聊）
- `DELETE /api/conversations/{conversation_id}/participants/{participant_id}` - 移除参与者

#### 消息管理
- `GET /api/conversations/{conversation_id}/messages` - 获取消息列表（分页）
- `POST /api/conversations/{conversation_id}/messages` - 发送消息
  ```json
  {
    "content": "消息内容",
    "message_type": "text",
    "reply_to_message_id": "可选的回复消息ID",
    "metadata": {}
  }
  ```
- `PUT /api/messages/{message_id}` - 编辑消息
- `DELETE /api/messages/{message_id}` - 删除消息（软删除）
- `POST /api/messages/{message_id}/read` - 标记消息为已读
- `POST /api/conversations/{conversation_id}/read` - 标记会话所有消息为已读

#### 未读消息
- `GET /api/conversations/unread` - 获取所有未读会话
- `GET /api/conversations/{conversation_id}/unread-count` - 获取会话未读数
- `GET /api/messages/unread-count` - 获取总未读消息数

#### Agent触发器管理（管理员功能）
- `GET /api/agents/{agent_id}/triggers` - 获取Agent的触发器列表
- `POST /api/agents/{agent_id}/triggers` - 创建触发器
- `PUT /api/agents/{agent_id}/triggers/{trigger_id}` - 更新触发器
- `DELETE /api/agents/{agent_id}/triggers/{trigger_id}` - 删除触发器

### WebSocket API

#### 连接端点
```
WS /api/ws/chat?token={jwt_token}
```

#### 客户端发送事件
```json
// 发送消息
{
  "type": "send_message",
  "data": {
    "conversation_id": "uuid",
    "content": "消息内容",
    "message_type": "text"
  }
}

// 标记已读
{
  "type": "mark_read",
  "data": {
    "conversation_id": "uuid",
    "message_id": "uuid"
  }
}

// 输入状态（正在输入...）
{
  "type": "typing",
  "data": {
    "conversation_id": "uuid",
    "is_typing": true
  }
}
```

#### 服务器推送事件
```json
// 新消息
{
  "type": "new_message",
  "data": {
    "conversation_id": "uuid",
    "message": {
      "id": "uuid",
      "sender_type": "agent",
      "sender_id": "uuid",
      "content": "消息内容",
      "created_at": "2026-03-15T10:00:00Z"
    }
  }
}

// 消息已读
{
  "type": "message_read",
  "data": {
    "message_id": "uuid",
    "reader_type": "user",
    "reader_id": "uuid",
    "read_at": "2026-03-15T10:00:00Z"
  }
}

// 对方正在输入
{
  "type": "typing_indicator",
  "data": {
    "conversation_id": "uuid",
    "participant_type": "agent",
    "participant_id": "uuid",
    "is_typing": true
  }
}

// Agent主动发起的消息
{
  "type": "agent_initiated_message",
  "data": {
    "conversation_id": "uuid",  // 可能是新创建的会话
    "message": {...}
  }
}
```

## Agent主动消息机制

### 触发器类型

#### 1. 定时触发（Scheduled Trigger）
```json
{
  "trigger_type": "scheduled",
  "trigger_config": {
    "cron": "0 9 * * *",  // 每天早上9点
    "timezone": "Asia/Shanghai",
    "message_template": "早上好！今天有什么我可以帮助你的吗？"
  },
  "target_type": "user",
  "target_id": "user_uuid"
}
```

#### 2. 事件触发（Event-Based Trigger）
```json
{
  "trigger_type": "event_based",
  "trigger_config": {
    "event": "user_inactive",  // 用户长时间未活动
    "threshold": "7d",  // 7天
    "message_template": "好久不见！最近怎么样？"
  },
  "target_type": "user",
  "target_id": "user_uuid"
}
```

#### 3. 关键词触发（Keyword Trigger）
```json
{
  "trigger_type": "keyword",
  "trigger_config": {
    "keywords": ["帮助", "help", "问题"],
    "context": "any_conversation",  // 或 "specific_conversation"
    "auto_reply": true,
    "message_template": "我注意到你需要帮助，有什么我可以协助的吗？"
  }
}
```

#### 4. 上下文变化触发（Context Change Trigger）
```json
{
  "trigger_type": "context_change",
  "trigger_config": {
    "watch": "user_location",  // 监控用户位置变化
    "condition": "near_cultural_site",
    "message_template": "我注意到你在{location}附近，这里有很多有趣的文化景点！"
  },
  "target_type": "user",
  "target_id": "user_uuid"
}
```

### Agent消息生成流程

```
1. 触发器检测 → 2. 触发条件满足 → 3. 调用Agent服务生成消息 → 4. 创建/获取会话 → 5. 发送消息 → 6. WebSocket推送
```

**详细步骤**：

1. **触发器检测**：
   - 后台任务定期检查所有active的触发器
   - 使用APScheduler或Celery Beat

2. **触发条件满足**：
   - 评估触发器配置的条件
   - 检查目标用户/Agent的状态

3. **调用Agent服务生成消息**：
   - 如果是简单的模板消息，直接使用
   - 如果需要AI生成，调用agent项目的API
   - 传递上下文信息（用户历史、当前状态等）

4. **创建/获取会话**：
   - 检查是否已存在与目标的会话
   - 如果不存在，创建新会话
   - 添加Agent和目标为参与者

5. **发送消息**：
   - 创建message记录
   - 更新conversation的last_message_at

6. **WebSocket推送**：
   - 查找目标的活跃WebSocket连接
   - 推送消息事件
   - 如果目标不在线，消息会在下次连接时拉取

### Agent间通信流程

```
Agent A → 生成消息 → 发送到共享会话 → Agent B接收 → 处理并回复
```

**实现方式**：
1. Agent A通过API发送消息到会话
2. 系统触发Agent B的webhook或轮询机制
3. Agent B处理消息并生成回复
4. 回复通过相同的消息系统发送

## 技术栈更新

### 新增依赖

```toml
dependencies = [
    # ... 原有依赖 ...
    "websockets>=12.0",           # WebSocket支持
    "python-socketio>=5.11.0",    # Socket.IO（可选，更好的浏览器兼容性）
    "redis>=5.0.0",               # 用于WebSocket连接管理和消息队列
    "celery>=5.3.0",              # 异步任务队列
    "apscheduler>=3.10.0",        # 定时任务调度
    "aioredis>=2.0.0",            # 异步Redis客户端
]
```

### 架构组件

1. **WebSocket服务器**：
   - 使用FastAPI的WebSocket支持
   - 连接管理器维护活跃连接
   - 支持房间（room）概念，每个会话是一个房间

2. **消息队列**：
   - Redis作为消息代理
   - Celery处理异步任务（Agent消息生成、触发器检查）

3. **连接状态管理**：
   - Redis存储用户/Agent的在线状态
   - 支持多实例部署（通过Redis Pub/Sub）

4. **触发器调度器**：
   - APScheduler管理定时触发器
   - Celery Beat处理周期性任务

## 实现流程

### Phase 1: 基础消息系统（3-4天）

**任务**：
1. 创建数据库表（conversations, conversation_participants, messages, message_read_status）
2. 实现Messaging领域层（实体、值对象、仓储接口）
3. 实现应用层（Commands、Queries、DTOs）
4. 实现基础设施层（PostgreSQL仓储实现）
5. 实现REST API端点（会话和消息CRUD）
6. 编写单元测试

**交付物**：
- 完整的消息数据模型
- 会话和消息管理API
- 支持User-User、User-Agent、Agent-Agent通信

### Phase 2: WebSocket实时通信（2-3天）

**任务**：
1. 实现WebSocket连接管理器
2. 实现消息广播器
3. 实现WebSocket事件处理（send_message, mark_read, typing）
4. 集成Redis进行连接状态管理
5. 实现多实例支持（Redis Pub/Sub）
6. 前端WebSocket客户端集成测试

**交付物**：
- WebSocket API端点
- 实时消息推送功能
- 在线状态管理

### Phase 3: Agent主动消息（2-3天）

**任务**：
1. 创建agent_triggers表
2. 实现触发器管理API
3. 实现触发器处理器（定时、事件、关键词、上下文）
4. 集成Celery和APScheduler
5. 实现Agent消息生成服务（调用agent项目API）
6. 实现Agent间通信机制
7. 编写触发器测试用例

**交付物**：
- Agent触发器管理系统
- Agent主动消息功能
- Agent间通信支持

### Phase 4: 优化和完善（1-2天）

**任务**：
1. 实现消息搜索功能
2. 实现消息分页优化
3. 添加消息缓存（Redis）
4. 性能测试和优化
5. 完善错误处理
6. 完善API文档

**交付物**：
- 优化的消息系统
- 完整的API文档
- 性能测试报告

## 与现有系统的集成

### 与Agent项目的集成

**原有方式**（代理转发）：
```
web-app → cultrue → agent项目
```

**新方式**（消息系统）：
```
web-app → cultrue消息系统 → 存储到数据库 → 触发Agent处理 → agent项目生成回复 → 存储到数据库 → WebSocket推送
```

**集成策略**：
1. **保留代理转发**：用于流式响应（SSE）
2. **新增消息系统**：用于持久化存储和多方通信
3. **混合模式**：
   - 用户发送消息 → 保存到cultrue消息系统
   - 同时转发到agent项目获取实时响应
   - Agent响应 → 保存到cultrue消息系统
   - 通过WebSocket推送给所有参与者

### 数据迁移

如果agent项目已有conversations数据：
1. 编写迁移脚本
2. 将agent项目的conversations迁移到cultrue的conversations表
3. 将messages从JSONB格式迁移到messages表
4. 建立participant关联

## 安全考虑

1. **WebSocket认证**：
   - 连接时验证JWT token
   - 定期刷新token

2. **权限控制**：
   - 只能发送消息到自己参与的会话
   - 只能读取自己参与的会话消息

3. **消息验证**：
   - 内容长度限制
   - 频率限制（防止刷屏）
   - 敏感词过滤

4. **Agent触发器权限**：
   - 只有管理员可以创建/修改触发器
   - Agent只能向授权的用户发送消息

## 性能优化

1. **消息分页**：
   - 使用游标分页（cursor-based pagination）
   - 默认每页50条消息

2. **缓存策略**：
   - Redis缓存最近的会话列表
   - Redis缓存未读消息计数
   - Redis缓存在线用户列表

3. **数据库优化**：
   - 合理使用索引
   - 定期归档旧消息
   - 使用数据库分区（按时间）

4. **WebSocket优化**：
   - 连接池管理
   - 心跳检测
   - 自动重连机制

## 监控和日志

1. **关键指标**：
   - WebSocket连接数
   - 消息发送/接收速率
   - Agent触发器执行次数
   - 消息延迟

2. **日志记录**：
   - 所有消息发送/接收
   - Agent触发器执行
   - WebSocket连接/断开
   - 错误和异常

## 下一步行动

1. ✅ 确认消息系统设计
2. ⬜ 更新主开发计划文档
3. ⬜ 开始实现Phase 1：基础消息系统
4. ⬜ 与前端团队对齐WebSocket协议
5. ⬜ 与Agent项目团队对齐集成方案
