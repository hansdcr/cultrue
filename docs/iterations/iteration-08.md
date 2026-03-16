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
- [ ] 创建AddMemberCommand和Handler
- [ ] 创建RemoveMemberCommand和Handler
- [ ] 创建ArchiveConversationCommand和Handler
- [ ] 创建ConversationDTO

**交付物**:
- `src/application/messaging/commands/create_conversation_command.py`
- `src/application/messaging/commands/add_member_command.py`
- `src/application/messaging/commands/remove_member_command.py`
- `src/application/messaging/commands/archive_conversation_command.py`
- `src/application/messaging/queries/get_conversation_query.py`
- `src/application/messaging/queries/list_conversations_query.py`
- `src/application/messaging/dtos/conversation_dto.py`

**业务逻辑**:
```python
from src.domain.shared.value_objects.actor import Actor

# CreateConversationCommand
@dataclass
class CreateConversationCommand:
    conversation_type: str  # 'direct' or 'group'
    members: List[Actor]    # 使用Actor值对象
    title: Optional[str]
    creator: Actor

# 业务规则
- Direct会话必须有且仅有2个成员
- Group会话至少需要2个成员
- 检查Direct会话是否已存在（避免重复创建）
- 验证所有Actor是否有效（User或Agent存在）
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
from src.domain.shared.value_objects.actor import Actor

# SendMessageCommand
@dataclass
class SendMessageCommand:
    conversation_id: UUID
    sender: Actor           # 使用Actor值对象
    message_type: str
    content: str
    metadata: Optional[dict]

# 业务规则
- 验证发送者是会话成员
- 自动更新会话的message_count和last_message_at
- 验证Actor是否有效
```

### 3. Conversation REST API

**任务**:
- [ ] 创建ConversationSchema（Pydantic模型）
- [ ] 实现POST /api/conversations - 创建会话
- [ ] 实现GET /api/conversations - 获取会话列表
- [ ] 实现GET /api/conversations/{conversation_id} - 获取会话详情
- [ ] 实现POST /api/conversations/{conversation_id}/members - 添加成员
- [ ] 实现DELETE /api/conversations/{conversation_id}/members - 移除成员
- [ ] 实现PUT /api/conversations/{conversation_id}/archive - 归档会话
- [ ] 实现DELETE /api/conversations/{conversation_id} - 删除会话

**交付物**:
- `src/interfaces/api/schemas/conversation_schema.py`
- `src/interfaces/api/rest/conversation.py`

**API设计**:
```python
# ActorSchema（Pydantic模型）
class ActorSchema(BaseModel):
    actor_type: str  # 'user' or 'agent'
    actor_id: UUID

# CreateConversationRequest
class CreateConversationRequest(BaseModel):
    conversation_type: str  # 'direct' or 'group'
    members: List[ActorSchema]
    title: Optional[str] = None

# POST /api/conversations
# 请求: {
#   "conversation_type": "direct",
#   "members": [
#     {"actor_type": "user", "actor_id": "user_uuid"},
#     {"actor_type": "agent", "actor_id": "agent_uuid"}
#   ],
#   "title": "Chat with Hans"  # 可选
# }
# 响应: {
#   "code": 201,
#   "data": {
#     "id": "uuid",
#     "conversation_type": "direct",
#     "title": "Chat with Hans",
#     "members": [
#       {"actor_type": "user", "actor_id": "uuid"},
#       {"actor_type": "agent", "actor_id": "uuid"}
#     ],
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
# SendMessageRequest
class SendMessageRequest(BaseModel):
    message_type: str = "text"
    content: str
    metadata: Optional[dict] = None

# MessageResponse
class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender: ActorSchema  # 使用ActorSchema
    message_type: str
    content: str
    metadata: Optional[dict]
    created_at: datetime

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
#       "actor_type": "user",
#       "actor_id": "uuid"
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
- 只有成员可以查看会话
- 只有成员可以发送消息
- 只有创建者可以添加/移除成员（群聊）
- 只有成员可以归档/删除会话

# 消息权限
- 只有发送者可以删除消息
- 只有会话成员可以查看消息

# 权限验证示例
async def verify_conversation_member(
    conversation_id: UUID,
    current_actor: Actor,
    conversation_repo: ConversationRepository
) -> Conversation:
    """验证当前Actor是否为会话成员。"""
    conversation = await conversation_repo.find_by_id(conversation_id)
    if not conversation:
        raise NotFoundException("Conversation not found")

    if not conversation.has_member(current_actor):
        raise ForbiddenException("Not a member of this conversation")

    return conversation
```

### 6. Actor验证服务

**任务**:
- [ ] 创建ActorValidationService
- [ ] 实现Actor存在性验证
- [ ] 实现批量Actor验证

**交付物**:
- `src/application/messaging/services/actor_validation_service.py`

**实现要点**:
```python
class ActorValidationService:
    """Actor验证服务。"""

    def __init__(
        self,
        user_repository: UserRepository,
        agent_repository: AgentRepository
    ):
        self.user_repository = user_repository
        self.agent_repository = agent_repository

    async def validate_actor(self, actor: Actor) -> bool:
        """验证Actor是否存在。"""
        if actor.is_user():
            user = await self.user_repository.find_by_id(actor.actor_id)
            return user is not None and user.is_active
        else:
            agent = await self.agent_repository.find_by_id(actor.actor_id)
            return agent is not None and agent.is_active

    async def validate_actors(self, actors: List[Actor]) -> None:
        """批量验证Actors，如果有无效的则抛出异常。"""
        for actor in actors:
            if not await self.validate_actor(actor):
                raise ValidationException(
                    f"Invalid actor: {actor.actor_type}:{actor.actor_id}"
                )

    async def get_actor_display_info(self, actor: Actor) -> dict:
        """获取Actor的显示信息（名称、头像等）。"""
        if actor.is_user():
            user = await self.user_repository.find_by_id(actor.actor_id)
            return {
                "actor_type": "user",
                "actor_id": str(user.id),
                "display_name": user.full_name or user.username,
                "avatar_url": user.avatar_url
            }
        else:
            agent = await self.agent_repository.find_by_id(actor.actor_id)
            return {
                "actor_type": "agent",
                "actor_id": str(agent.id),
                "display_name": agent.name,
                "avatar_url": agent.avatar
            }
```

### 7. 集成到main.py

**任务**:
- [ ] 注册conversation路由
- [ ] 注册message路由
- [ ] 测试完整流程

**交付物**:
- 更新 `main.py`

### 8. 测试

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
async def test_user_agent_conversation(client, auth_headers):
    # 1. 创建会话
    response = await client.post("/api/conversations", json={
        "conversation_type": "direct",
        "members": [
            {"actor_type": "user", "actor_id": str(user_id)},
            {"actor_type": "agent", "actor_id": str(agent_id)}
        ]
    }, headers=auth_headers)
    assert response.status_code == 201
    conversation_id = response.json()["data"]["id"]

    # 2. 发送消息
    response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": "Hello Hans!"},
        headers=auth_headers
    )
    assert response.status_code == 201

    # 3. 查询消息历史
    response = await client.get(
        f"/api/conversations/{conversation_id}/messages",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) == 1

# 场景2: User创建与另一个User的会话
async def test_user_user_conversation(client, auth_headers):
    response = await client.post("/api/conversations", json={
        "conversation_type": "direct",
        "members": [
            {"actor_type": "user", "actor_id": str(user1_id)},
            {"actor_type": "user", "actor_id": str(user2_id)}
        ]
    }, headers=auth_headers)
    assert response.status_code == 201

# 场景3: 创建群聊
async def test_group_conversation(client, auth_headers):
    response = await client.post("/api/conversations", json={
        "conversation_type": "group",
        "members": [
            {"actor_type": "user", "actor_id": str(user_id)},
            {"actor_type": "agent", "actor_id": str(agent1_id)},
            {"actor_type": "agent", "actor_id": str(agent2_id)}
        ],
        "title": "Study Group"
    }, headers=auth_headers)
    assert response.status_code == 201

# 场景4: 权限测试 - 非成员无法查看会话
async def test_non_member_cannot_view_conversation(client, auth_headers):
    # user1创建与agent的会话
    response = await client.post("/api/conversations", json={
        "conversation_type": "direct",
        "members": [
            {"actor_type": "user", "actor_id": str(user1_id)},
            {"actor_type": "agent", "actor_id": str(agent_id)}
        ]
    }, headers=auth_headers_user1)
    conversation_id = response.json()["data"]["id"]

    # user2尝试查看会话（应该失败）
    response = await client.get(
        f"/api/conversations/{conversation_id}",
        headers=auth_headers_user2
    )
    assert response.status_code == 403
```

## ✅ 验收标准

- [ ] 可以创建Direct会话（User ↔ User, User ↔ Agent, Agent ↔ Agent）
- [ ] 可以创建Group会话
- [ ] 可以发送和接收消息
- [ ] 可以查询会话列表（支持分页）
- [ ] 可以查询消息历史（支持分页）
- [ ] 可以添加/移除群聊成员
- [ ] 可以归档/删除会话
- [ ] Actor验证正确
- [ ] 权限控制正确
- [ ] 所有测试通过
- [ ] API文档完整
- [ ] 与迭代6、7的Actor模型保持一致

## 🔧 技术要点

### 1. Actor验证

由于Actor是值对象，需要在应用层验证其有效性：
```python
# 在CreateConversationCommandHandler中
async def handle(self, command: CreateConversationCommand) -> ConversationDTO:
    # 验证所有成员是否有效
    await self.actor_validation_service.validate_actors(command.members)

    # 创建会话
    conversation = Conversation.create_direct(
        command.members[0],
        command.members[1]
    )

    # 保存
    saved = await self.conversation_repository.save(conversation)
    return ConversationDTO.from_entity(saved)
```

### 2. 避免重复创建Direct会话

创建Direct会话前检查是否已存在：
```python
existing = await conversation_repo.find_direct_conversation(
    actor1, actor2
)
if existing and existing.status == ConversationStatus.ACTIVE:
    return ConversationDTO.from_entity(existing)
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
conversations = await conversation_repo.find_by_actor(
    current_actor, limit=20, offset=0
)
# 仓储内部实现: ORDER BY last_message_at DESC
```

### 5. 未读消息计数

在conversation_members表中记录last_read_at：
```python
# 获取未读消息数
async def get_unread_count(
    conversation_id: UUID,
    actor: Actor
) -> int:
    member = await get_conversation_member(conversation_id, actor)
    if not member or not member.last_read_at:
        return await count_messages(conversation_id)
    return await count_messages_after(
        conversation_id,
        member.last_read_at
    )
```

### 6. 当前用户Actor的获取

从认证中间件注入的user_id创建Actor：
```python
# 依赖注入
async def get_current_actor(
    request: Request,
    user_repository: UserRepository = Depends(get_user_repository)
) -> Actor:
    """从请求中获取当前用户的Actor。"""
    user_id = request.state.user_id  # 从认证中间件注入
    user = await user_repository.find_by_id(user_id)
    if not user:
        raise UnauthorizedException("User not found")
    return Actor.from_user(user_id)
```

### 7. DTO中的Actor序列化

```python
@dataclass
class ActorDTO:
    actor_type: str
    actor_id: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

@dataclass
class MessageDTO:
    id: str
    conversation_id: str
    sender: ActorDTO
    message_type: str
    content: str
    metadata: Optional[dict]
    created_at: str

    @classmethod
    async def from_entity(
        cls,
        message: Message,
        actor_validation_service: ActorValidationService
    ) -> "MessageDTO":
        # 获取发送者的显示信息
        sender_info = await actor_validation_service.get_actor_display_info(
            message.sender
        )

        return cls(
            id=str(message.id),
            conversation_id=str(message.conversation_id),
            sender=ActorDTO(**sender_info),
            message_type=message.message_type.value,
            content=message.content,
            metadata=message.metadata,
            created_at=message.created_at.isoformat()
        )
```

## 🔜 下一步

完成迭代8后，进入**迭代9: WebSocket实时通信**，实现实时消息推送。

## 📊 预期成果

完成本迭代后，系统将具备：
- ✅ 完整的会话管理API
- ✅ 完整的消息管理API
- ✅ 支持多种通信类型（User-User, User-Agent, Agent-Agent）
- ✅ Actor验证机制
- ✅ 权限控制
- ✅ 完整的测试覆盖
- ✅ 与迭代6、7保持架构一致性

---

**创建日期**: 2026-03-16
**修订日期**: 2026-03-16
**修订原因**: 采用Solution C的Actor模型，移除Participant实体依赖
