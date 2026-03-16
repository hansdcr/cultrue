# 快速实施指南

> 采用Participant中间表 + Agent独立认证方案的快速参考

## 🎯 核心概念

### Actor vs Participant

```python
# Actor：领域层值对象（应用层使用）
actor = Actor.from_user(user_id)
actor = Actor.from_agent(agent_id)

# Participant：数据库层实体（仓储层使用）
participant = Participant.from_actor(actor)
actor = participant.to_actor()
```

### 自动转换

```python
# 应用层代码（使用Actor）
contact = Contact.create(owner=actor, target=target_actor)
await contact_repo.save(contact)

# 仓储层自动处理
# 1. find_or_create(owner) → owner_participant
# 2. find_or_create(target) → target_participant
# 3. save ContactModel(owner_id=owner_participant.id, ...)
```

## 📁 文件结构

```
src/
├── domain/
│   ├── shared/
│   │   └── value_objects/
│   │       └── actor.py                    # Actor值对象
│   ├── participant/                        # ⭐ 新增
│   │   ├── entities/
│   │   │   └── participant.py              # Participant实体
│   │   └── repositories/
│   │       └── participant_repository.py   # Participant仓储接口
│   ├── agent/
│   │   ├── entities/
│   │   │   └── agent.py                    # Agent实体（含api_key_hash）
│   │   └── value_objects/
│   │       └── api_key.py                  # ⭐ 新增：ApiKey值对象
│   ├── contact/
│   │   └── entities/
│   │       └── contact.py                  # Contact实体（使用Actor）
│   ├── messaging/
│   │   ├── entities/
│   │   │   ├── conversation.py             # Conversation实体（使用Actor）
│   │   │   └── message.py                  # Message实体（使用Actor）
│
├── application/
│   ├── agent/
│   │   └── commands/
│   │       ├── register_agent_command.py   # ⭐ 新增：Agent注册
│   │       └── regenerate_api_key_command.py # ⭐ 新增
│   ├── contact/
│   │   └── commands/
│   │       └── add_contact_command.py      # 使用Actor
│   ├── messaging/
│   │   └── commands/
│   │       ├── create_conversation_command.py  # 使用Actor
│   │       └── send_message_command.py         # 使用Actor
│
├── infrastructure/
│   ├── persistence/
│   │   ├── models/
│   │   │   ├── participant_model.py        # ⭐ 新增
│   │   │   ├── contact_model.py            # 使用participant_id外键
│   │   │   ├── conversation_member_model.py # 使用participant_id外键
│   │   │   └── message_model.py            # 使用sender_id外键
│   │   └── repositories/
│   │       ├── postgres_participant_repository.py  # ⭐ 新增
│   │       ├── postgres_contact_repository.py      # 注入participant_repo
│   │       ├── postgres_conversation_repository.py # 注入participant_repo
│   │       └── postgres_message_repository.py      # 注入participant_repo
│   └── security/
│       ├── api_key_service.py              # ⭐ 新增：API Key验证
│       └── auth_middleware.py              # ⭐ 更新：支持ApiKey认证
│
└── interfaces/
    └── api/
        └── rest/
            ├── agent.py                    # ⭐ 新增：/api/agents/register
            ├── contact.py                  # 使用ActorSchema
            ├── conversation.py             # 使用ActorSchema
            └── message.py                  # 使用ActorSchema
```

## 🔧 关键代码模板

### 1. Participant实体

```python
@dataclass
class Participant:
    id: UUID
    participant_type: ActorType
    user_id: Optional[UUID]
    agent_id: Optional[UUID]
    created_at: datetime

    @classmethod
    def from_actor(cls, actor: Actor) -> "Participant":
        if actor.is_user():
            return cls(id=uuid4(), participant_type=ActorType.USER,
                      user_id=actor.actor_id, agent_id=None, ...)
        else:
            return cls(id=uuid4(), participant_type=ActorType.AGENT,
                      user_id=None, agent_id=actor.actor_id, ...)

    def to_actor(self) -> Actor:
        if self.participant_type == ActorType.USER:
            return Actor.from_user(self.user_id)
        else:
            return Actor.from_agent(self.agent_id)
```

### 2. ParticipantRepository

```python
class PostgresParticipantRepository:
    async def find_or_create(self, actor: Actor) -> Participant:
        # 1. 尝试查找
        participant = await self.find_by_actor(actor)

        # 2. 不存在则创建
        if not participant:
            participant = Participant.from_actor(actor)
            model = self._to_model(participant)
            self.session.add(model)
            await self.session.flush()
            await self.session.refresh(model)
            participant = self._to_entity(model)

        return participant
```

### 3. 使用Participant的仓储模板

```python
class PostgresXxxRepository:
    def __init__(self, session, participant_repo):
        self.session = session
        self.participant_repo = participant_repo

    async def save(self, entity):
        # 确保Participant存在
        participant = await self.participant_repo.find_or_create(entity.actor)

        # 使用participant.id保存
        model = XxxModel(participant_id=participant.id, ...)
        self.session.add(model)
        await self.session.flush()
        return entity

    async def find_by_actor(self, actor: Actor):
        # 查找Participant
        participant = await self.participant_repo.find_by_actor(actor)
        if not participant:
            return None

        # 使用participant.id查询
        result = await self.session.execute(
            select(XxxModel)
            .where(XxxModel.participant_id == participant.id)
            .options(joinedload(XxxModel.participant))
        )

        # 转换回Actor
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    def _to_entity(self, model):
        actor = model.participant.to_actor()
        return Entity(actor=actor, ...)
```

### 4. Agent注册

```python
# Command
@dataclass
class RegisterAgentCommand:
    agent_id: str
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None

# Handler
class RegisterAgentCommandHandler:
    async def handle(self, command):
        # 生成API Key
        api_key = ApiKey.generate()
        api_key_hash = self.password_hasher.hash(api_key.value)

        # 创建Agent
        agent = Agent(
            id=uuid4(),
            agent_id=AgentId(command.agent_id),
            name=command.name,
            api_key_hash=api_key_hash,
            ...
        )

        # 保存
        saved_agent = await self.agent_repo.save(agent)

        return RegisterAgentResult(agent=saved_agent, api_key=api_key)
```

### 5. 认证中间件

```python
async def auth_middleware(request: Request):
    auth_header = request.headers.get("Authorization")

    if auth_header.startswith("Bearer "):
        # User JWT
        token = auth_header[7:]
        payload = verify_jwt_token(token)
        user_id = UUID(payload["sub"])
        request.state.actor = Actor.from_user(user_id)

    elif auth_header.startswith("ApiKey "):
        # Agent API Key
        api_key = auth_header[7:]
        agent = await api_key_service.verify_api_key(api_key)
        if not agent:
            raise UnauthorizedException("Invalid API Key")
        request.state.actor = Actor.from_agent(agent.id)

    else:
        raise UnauthorizedException("Invalid auth header")
```

## 📊 数据库表

### participants表

```sql
CREATE TABLE participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    participant_type VARCHAR(20) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_participant_type CHECK (
        (participant_type = 'user' AND user_id IS NOT NULL AND agent_id IS NULL) OR
        (participant_type = 'agent' AND agent_id IS NOT NULL AND user_id IS NULL)
    ),
    CONSTRAINT unique_user_participant UNIQUE (user_id),
    CONSTRAINT unique_agent_participant UNIQUE (agent_id)
);
```

### agents表（添加api_key_hash）

```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL,  -- ⭐ 新增
    ...
);
```

### contacts表（使用外键）

```sql
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    ...
);
```

### conversation_members表（使用外键）

```sql
CREATE TABLE conversation_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    participant_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    ...
);
```

### messages表（使用外键）

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    ...
);
```

## 🧪 测试示例

### 测试外键约束

```python
async def test_cannot_create_contact_with_invalid_actor():
    """测试：无法创建不存在Actor的Contact。"""
    invalid_actor = Actor.from_user(uuid4())  # 不存在的user_id
    valid_actor = Actor.from_user(existing_user.id)

    contact = Contact.create(owner=valid_actor, target=invalid_actor)

    # 应该抛出外键约束错误
    with pytest.raises(IntegrityError):
        await contact_repo.save(contact)
```

### 测试级联删除

```python
async def test_cascade_delete_when_user_deleted():
    """测试：删除User时级联删除相关记录。"""
    # 1. 创建Contact
    user_actor = Actor.from_user(user.id)
    agent_actor = Actor.from_agent(agent.id)
    contact = Contact.create(owner=user_actor, target=agent_actor)
    await contact_repo.save(contact)

    # 2. 删除User
    await user_repo.delete(user.id)

    # 3. Participant和Contact应该被级联删除
    participant = await participant_repo.find_by_actor(user_actor)
    assert participant is None

    contacts = await contact_repo.find_by_owner(user_actor)
    assert len(contacts) == 0
```

### 测试Agent认证

```python
async def test_agent_authentication():
    """测试：Agent使用API Key认证。"""
    # 1. 注册Agent
    command = RegisterAgentCommand(
        agent_id="agent_test",
        name="Test Agent"
    )
    result = await register_handler.handle(command)
    api_key = result.api_key.value

    # 2. 使用API Key调用API
    response = client.post(
        "/api/contacts",
        headers={"Authorization": f"ApiKey {api_key}"},
        json={
            "target_type": "user",
            "target_id": str(user.id),
            "contact_type": "friend"
        }
    )

    assert response.status_code == 201
```

## 📝 实施检查清单

### 迭代6
- [ ] 创建Participant领域层（实体、仓储接口）
- [ ] 创建ApiKey值对象
- [ ] 更新Agent实体（添加api_key_hash）
- [ ] 创建participants表迁移
- [ ] 更新agents表迁移（添加api_key_hash）
- [ ] 更新contacts表迁移（使用外键）
- [ ] 实现PostgresParticipantRepository
- [ ] 更新PostgresContactRepository（注入participant_repo）
- [ ] 实现RegisterAgentCommand和Handler
- [ ] 实现ApiKeyService
- [ ] 更新AuthMiddleware（支持ApiKey）
- [ ] 创建Agent注册API
- [ ] 测试

### 迭代7
- [ ] 更新conversation_members表迁移（使用外键）
- [ ] 更新messages表迁移（使用外键）
- [ ] 更新PostgresConversationRepository
- [ ] 更新PostgresMessageRepository
- [ ] 测试

### 迭代8
- [ ] 移除ActorValidationService
- [ ] 简化Command Handler
- [ ] 更新API文档
- [ ] 测试

## 🚨 常见问题

### Q1: Participant什么时候创建？
A: 仓储层save时自动调用find_or_create，应用层无需关心。

### Q2: 如果Actor不存在会怎样？
A: find_or_create会尝试创建Participant，但外键约束会失败，抛出IntegrityError。

### Q3: 应用层需要修改吗？
A: 不需要。应用层继续使用Actor，仓储层自动处理转换。

### Q4: 性能会受影响吗？
A: 不会。find_or_create有查询缓存，且减少了应用层验证查询。

### Q5: 如何调试外键错误？
A: 数据库会明确指出哪个外键约束失败，比应用层验证更容易定位问题。

---

**创建日期**: 2026-03-16
**适用版本**: v3 (双层抽象 + Agent独立认证)
