# 迭代8: 消息系统-基础API

> 实现会话和消息的CRUD API接口

## 📋 迭代信息

- **迭代编号**: 8
- **预计时间**: 1-2天
- **当前状态**: 🟡 计划中
- **依赖迭代**: 迭代7 ✅
- **开始日期**: 待定

## 🎯 迭代目标

实现会话和消息的应用层业务逻辑和REST API接口，支持创建会话、发送消息、查询历史等核心功能。

## 📝 任务清单

### 1. Conversation应用层

**任务**:
- [ ] 创建CreateConversationCommand和Handler
- [ ] 创建GetConversationQuery和Handler
- [ ] 创建ListConversationsQuery和Handler
- [ ] 创建AddParticipantCommand和Handler
- [ ] 创建RemoveParticipantCommand和Handler
- [ ] 创建ArchiveConversationCommand和Handler
- [ ] 创建ConversationDTO

**交付物**:
- `src/application/messaging/commands/create_conversation_command.py`
- `src/application/messaging/commands/add_participant_command.py`
- `src/application/messaging/commands/remove_participant_command.py`
- `src/application/messaging/commands/archive_conversation_command.py`
- `src/application/messaging/queries/get_conversation_query.py`
- `src/application/messaging/queries/list_conversations_query.py`
- `src/application/messaging/dtos/conversation_dto.py`

**业务逻辑**:
```python
# CreateConversationCommand
class CreateConversationCommand:
    conversation_type: str  # 'direct' or 'group'
    participant_ids: List[UUID]
    title: Optional[str]
    creator_id: UUID

# 业务规则
- Direct会话必须有且仅有2个参与者
- Group会话至少需要2个参与者
- 检查Direct会话是否已存在（避免重复创建）
- 自动创建Participant记录（如果不存在）
```

### 2. Message应用层

**任务**:
- [ ] 创建SendMessageCommand和Handler
- [ ] 创建GetMessageQuery和Handler
- [ ] 创建ListMessagesQuery和Handler
- [ ] 创建DeleteMessageCommand和Handler
- [ ] 创建MessageDTO

**交付物**:
- `src/application/messaging/commands/send_message_command.py`
- `src/application/messaging/commands/delete_message_command.py`
- `src/application/messaging/queries/get_message_query.py`
- `src/application/messaging/queries/list_messages_query.py`
- `src/application/messaging/dtos/message_dto.py`

**业务逻辑**:
```python
# SendMessageCommand
class SendMessageCommand:
    conversation_id: UUID
    sender_id: UUID  # user_id or agent_id
    sender_type: str  # 'user' or 'agent'
    message_type: str
    content: str
    metadata: Optional[dict]

# 业务规则
- 验证发送者是会话参与者
- 自动更新会话的message_count和last_message_at
- 自动创建Participant（如果不存在）
```

### 3. Conversation REST API

**任务**:
- [ ] 创建ConversationSchema（Pydantic模型）
- [ ] 实现POST /api/conversations - 创建会话
- [ ] 实现GET /api/conversations - 获取会话列表
- [ ] 实现GET /api/conversations/{conversation_id} - 获取会话详情
- [ ] 实现POST /api/conversations/{conversation_id}/participants - 添加参与者
- [ ] 实现DELETE /api/conversations/{conversation_id}/participants/{participant_id} - 移除参与者
- [ ] 实现PUT /api/conversations/{conversation_id}/archive - 归档会话
- [ ] 实现DELETE /api/conversations/{conversation_id} - 删除会话

**交付物**:
- `src/interfaces/api/schemas/conversation_schema.py`
- `src/interfaces/api/rest/conversation.py`

**API设计**:
```python
# POST /api/conversations
# 请求: {
#   "conversation_type": "direct",
#   "participant_ids": ["user_uuid", "agent_uuid"],
#   "title": "Chat with Hans"  # 可选
# }
# 响应: {
#   "code": 201,
#   "data": {
#     "id": "uuid",
#     "conversation_type": "direct",
#     "title": "Chat with Hans",
#     "participants": [...],
#     "message_count": 0,
#     "created_at": "2026-03-16T..."
#   }
# }

# GET /api/conversations?limit=20&offset=0
# 响应: {
#   "code": 200,
#   "data": {
#     "items": [...],
#     "total": 50,
#     "limit": 20,
#     "offset": 0
#   }
# }
```

### 4. Message REST API

**任务**:
- [ ] 创建MessageSchema（Pydantic模型）
- [ ] 实现POST /api/conversations/{conversation_id}/messages - 发送消息
- [ ] 实现GET /api/conversations/{conversation_id}/messages - 获取消息列表
- [ ] 实现GET /api/messages/{message_id} - 获取消息详情
- [ ] 实现DELETE /api/messages/{message_id} - 删除消息

**交付物**:
- `src/interfaces/api/schemas/message_schema.py`
- `src/interfaces/api/rest/message.py`

**API设计**:
```python
# POST /api/conversations/{conversation_id}/messages
# 请求: {
#   "message_type": "text",
#   "content": "Hello!",
#   "metadata": {}  # 可选
# }
# 响应: {
#   "code": 201,
#   "data": {
#     "id": "uuid",
#     "conversation_id": "uuid",
#     "sender": {
#       "id": "uuid",
#       "type": "user",
#       "display_name": "Alice"
#     },
#     "message_type": "text",
#     "content": "Hello!",
#     "created_at": "2026-03-16T..."
#   }
# }

# GET /api/conversations/{conversation_id}/messages?limit=50&offset=0
# 响应: {
#   "code": 200,
#   "data": {
#     "items": [...],
#     "total": 100,
#     "limit": 50,
#     "offset": 0
#   }
# }
```

### 5. 权限控制

**任务**:
- [ ] 实现会话权限验证
- [ ] 实现消息权限验证
- [ ] 创建权限依赖注入

**交付物**:
- `src/interfaces/api/dependencies/conversation_permissions.py`

**权限规则**:
```python
# 会话权限
- 只有参与者可以查看会话
- 只有参与者可以发送消息
- 只有创建者可以添加/移除参与者（群聊）
- 只有参与者可以归档/删除会话

# 消息权限
- 只有发送者可以删除消息
- 只有会话参与者可以查看消息
```

### 6. 集成到main.py

**任务**:
- [ ] 注册conversation路由
- [ ] 注册message路由
- [ ] 测试完整流程

**交付物**:
- 更新 `main.py`

### 7. 测试

**任务**:
- [ ] 编写应用层单元测试
- [ ] 编写API集成测试
- [ ] 测试多种通信场景
- [ ] 测试权限控制

**交付物**:
- `tests/unit/application/messaging/test_create_conversation_command.py`
- `tests/unit/application/messaging/test_send_message_command.py`
- `tests/integration/test_conversation_api.py`
- `tests/integration/test_message_api.py`

**测试场景**:
```python
# 场景1: User创建与Agent的会话并发送消息
def test_user_agent_conversation():
    # 1. 创建会话
    response = client.post("/api/conversations", json={
        "conversation_type": "direct",
        "participant_ids": [user_id, agent_id]
    })
    conversation_id = response.json()["data"]["id"]

    # 2. 发送消息
    response = client.post(f"/api/conversations/{conversation_id}/messages", json={
        "content": "Hello Hans!"
    })

    # 3. 查询消息历史
    response = client.get(f"/api/conversations/{conversation_id}/messages")

# 场景2: User创建与另一个User的会话
def test_user_user_conversation():
    response = client.post("/api/conversations", json={
        "conversation_type": "direct",
        "participant_ids": [user1_id, user2_id]
    })

# 场景3: 创建群聊
def test_group_conversation():
    response = client.post("/api/conversations", json={
        "conversation_type": "group",
        "participant_ids": [user_id, agent1_id, agent2_id],
        "title": "Study Group"
    })
```

## ✅ 验收标准

- [ ] 可以创建Direct会话（User ↔ User, User ↔ Agent, Agent ↔ Agent）
- [ ] 可以创建Group会话
- [ ] 可以发送和接收消息
- [ ] 可以查询会话列表（支持分页）
- [ ] 可以查询消息历史（支持分页）
- [ ] 可以添加/移除群聊参与者
- [ ] 可以归档/删除会话
- [ ] 权限控制正确
- [ ] 所有测试通过
- [ ] API文档完整

## 🔧 技术要点

### 1. 自动创建Participant

当User或Agent首次参与会话时，自动创建Participant记录：
```python
async def _ensure_participant(self, user_id: UUID = None, agent_id: UUID = None):
    if user_id:
        user = await user_repo.find_by_id(user_id)
        return await participant_repo.find_or_create_from_user(
            user_id, user.full_name, user.avatar_url
        )
    elif agent_id:
        agent = await agent_repo.find_by_id(agent_id)
        return await participant_repo.find_or_create_from_agent(
            agent_id, agent.name, agent.avatar
        )
```

### 2. 避免重复创建Direct会话

创建Direct会话前检查是否已存在：
```python
existing = await conversation_repo.find_direct_conversation(
    participant1_id, participant2_id
)
if existing:
    return existing
```

### 3. 消息分页

使用游标分页或偏移分页：
```python
# 偏移分页
messages = await message_repo.find_by_conversation_id(
    conversation_id, limit=50, offset=0
)

# 游标分页（更高效）
messages = await message_repo.find_by_conversation_id_after(
    conversation_id, after_message_id=last_message_id, limit=50
)
```

### 4. 会话列表排序

按last_message_at降序排列，最近活跃的会话在前：
```python
conversations = await conversation_repo.find_by_participant_id(
    participant_id, limit=20, offset=0, order_by="last_message_at DESC"
)
```

### 5. 未读消息计数

在conversation_participants表中记录last_read_at：
```python
unread_count = await message_repo.count_unread(
    conversation_id, participant_id, last_read_at
)
```

## 🔜 下一步

完成迭代8后，进入**迭代9: WebSocket-基础**，实现实时消息推送。

## 📊 预期成果

完成本迭代后，系统将具备：
- ✅ 完整的会话管理API
- ✅ 完整的消息管理API
- ✅ 支持多种通信类型
- ✅ 权限控制
- ✅ 完整的测试覆盖

---

**创建日期**: 2026-03-16
