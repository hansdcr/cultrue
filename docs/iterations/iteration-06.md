# 迭代6: Agent管理（双层抽象架构）

> 实现Agent信息管理和通用的联系人关系系统

## 📋 迭代信息

- **迭代编号**: 6
- **预计时间**: 1-2天
- **当前状态**: 🟡 设计完成
- **依赖迭代**: 迭代5 ✅
- **开始日期**: 待定

## 🎯 迭代目标

实现Agent实体管理和统一的联系人关系系统，支持User-User、User-Agent、Agent-Agent之间的关系建模，为后续的消息系统打下基础。

## 💡 设计理念

**双层抽象架构（Actor + Participant）**

- **领域层**：使用Actor值对象统一表示User和Agent，保持领域模型简洁
- **数据库层**：使用Participant中间表，通过外键约束保证数据完整性
- **仓储层**：自动管理Actor ↔ Participant转换，对应用层透明
- **优势**：兼顾领域清晰性和数据完整性，无需应用层手动验证

## 📝 任务清单

### 1. Participant领域层（新增）

**任务**:
- [ ] 创建Participant实体
- [ ] 创建ParticipantRepository接口

**交付物**:
- `src/domain/participant/entities/participant.py`
- `src/domain/participant/repositories/participant_repository.py`

**设计要点**:
```python
# Participant实体（数据库映射层）
@dataclass
class Participant:
    """用于保证数据完整性的中间表实体。
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
            return cls(id=uuid4(), participant_type=ActorType.USER,
                      user_id=actor.actor_id, agent_id=None, ...)
        else:
            return cls(id=uuid4(), participant_type=ActorType.AGENT,
                      user_id=None, agent_id=actor.actor_id, ...)

    def to_actor(self) -> Actor:
        """转换为Actor。"""
        if self.participant_type == ActorType.USER:
            return Actor.from_user(self.user_id)
        else:
            return Actor.from_agent(self.agent_id)

# ParticipantRepository接口
class ParticipantRepository(ABC):
    @abstractmethod
    async def find_by_actor(self, actor: Actor) -> Optional[Participant]:
        pass

    @abstractmethod
    async def find_or_create(self, actor: Actor) -> Participant:
        """查找或创建Participant（核心方法）。"""
        pass
```

### 2. Agent领域层

**任务**:
- [ ] 创建AgentId值对象
- [ ] 创建ApiKey值对象（Agent独立认证）⭐ 新增
- [ ] 创建AgentConfig值对象（模型配置）
- [ ] 创建Agent实体（含api_key_hash字段）
- [ ] 创建AgentRepository接口
- [ ] 创建Actor值对象（统一User和Agent的标识）

**交付物**:
- `src/domain/agent/value_objects/agent_id.py`
- `src/domain/agent/value_objects/api_key.py` ⭐ 新增
- `src/domain/agent/value_objects/agent_config.py`
- `src/domain/agent/entities/agent.py`
- `src/domain/agent/repositories/agent_repository.py`
- `src/domain/shared/value_objects/actor.py`

**设计要点**:
```python
# Actor值对象（统一标识）
class ActorType(str, Enum):
    USER = "user"
    AGENT = "agent"

class Actor:
    """Actor值对象，统一表示User或Agent。"""
    actor_type: ActorType
    actor_id: UUID

    @classmethod
    def from_user(cls, user_id: UUID) -> "Actor":
        return cls(actor_type=ActorType.USER, actor_id=user_id)

    @classmethod
    def from_agent(cls, agent_id: UUID) -> "Actor":
        return cls(actor_type=ActorType.AGENT, actor_id=agent_id)

    def is_user(self) -> bool:
        return self.actor_type == ActorType.USER

    def is_agent(self) -> bool:
        return self.actor_type == ActorType.AGENT

# ApiKey值对象（Agent独立认证）⭐ 新增
class ApiKey:
    """Agent API Key值对象。

    格式: ak_<32-char-random-string>
    """
    def __init__(self, value: str):
        if not value.startswith('ak_'):
            raise ValueError("API Key must start with 'ak_'")
        self._value = value

    @classmethod
    def generate(cls) -> "ApiKey":
        """生成新的API Key。"""
        random_str = secrets.token_urlsafe(24)[:32]
        return cls(f"ak_{random_str}")

    def mask(self) -> str:
        """返回掩码版本（用于显示）。"""
        return f"{self._value[:10]}...{self._value[-4:]}"

# AgentId值对象
class AgentId:
    """Agent ID值对象。

    格式: agent_hans, agent_alice, agent_bob
    """
    def __init__(self, value: str):
        if not value.startswith('agent_'):
            raise ValueError("Agent ID must start with 'agent_'")
        self._value = value

# AgentConfig值对象
class AgentConfig:
    """Agent配置值对象。"""
    temperature: float = 0.7
    max_tokens: int = 2000
    model: str = "claude-sonnet-4"

# Agent实体
class Agent:
    """Agent实体。"""
    id: UUID
    agent_id: AgentId  # 唯一标识符
    name: str
    avatar: Optional[str]
    description: Optional[str]
    system_prompt: Optional[str]
    model_config: AgentConfig
    api_key_hash: str  # ⭐ 新增：API Key哈希值
    is_active: bool
    created_by: Optional[UUID]  # 创建者的user_id
    created_at: datetime
    updated_at: datetime

    def to_actor(self) -> Actor:
        """转换为Actor。"""
        return Actor.from_agent(self.id)

    def verify_api_key(self, api_key: ApiKey) -> bool:
        """验证API Key。"""
        return bcrypt.checkpw(api_key.value.encode(), self.api_key_hash.encode())

    def regenerate_api_key(self) -> ApiKey:
        """重新生成API Key。"""
        new_api_key = ApiKey.generate()
        self.api_key_hash = bcrypt.hashpw(new_api_key.value.encode(), bcrypt.gensalt()).decode()
        return new_api_key
```

### 2. Contact领域层（新增）

**任务**:
- [ ] 创建ContactType枚举
- [ ] 创建Contact实体
- [ ] 创建ContactRepository接口

**交付物**:
- `src/domain/contact/enums/contact_type.py`
- `src/domain/contact/entities/contact.py`
- `src/domain/contact/repositories/contact_repository.py`

**设计要点**:
```python
# ContactType枚举
class ContactType(str, Enum):
    FRIEND = "friend"        # 好友
    FAVORITE = "favorite"    # 收藏
    COLLEAGUE = "colleague"  # 同事
    BLOCKED = "blocked"      # 屏蔽

# Contact实体
class Contact:
    """联系人实体，支持User-User、User-Agent、Agent-Agent关系。"""
    id: UUID
    owner: Actor           # 拥有者（可以是User或Agent）
    target: Actor          # 目标（可以是User或Agent）
    contact_type: ContactType
    alias: Optional[str]   # 备注名
    is_favorite: bool
    last_interaction_at: Optional[datetime]
    created_at: datetime

    @classmethod
    def create(
        cls,
        owner: Actor,
        target: Actor,
        contact_type: ContactType = ContactType.FRIEND,
        alias: Optional[str] = None
    ) -> "Contact":
        """创建联系人关系。"""
        pass

    def update_alias(self, alias: str) -> None:
        """更新备注名。"""
        pass

    def mark_as_favorite(self) -> None:
        """标记为收藏。"""
        self.is_favorite = True

    def record_interaction(self) -> None:
        """记录交互时间。"""
        self.last_interaction_at = datetime.now(timezone.utc)
```

### 3. Agent应用层

**任务**:
- [ ] 创建RegisterAgentCommand和Handler（Agent注册）⭐ 新增
- [ ] 创建RegenerateApiKeyCommand和Handler ⭐ 新增
- [ ] 创建CreateAgentCommand和Handler（管理员创建）
- [ ] 创建UpdateAgentCommand和Handler
- [ ] 创建GetAgentQuery和Handler
- [ ] 创建ListAgentsQuery和Handler
- [ ] 创建AgentDTO

**交付物**:
- `src/application/agent/commands/register_agent_command.py` ⭐ 新增
- `src/application/agent/commands/regenerate_api_key_command.py` ⭐ 新增
- `src/application/agent/commands/create_agent_command.py`
- `src/application/agent/commands/update_agent_command.py`
- `src/application/agent/queries/get_agent_query.py`
- `src/application/agent/queries/list_agents_query.py`
- `src/application/agent/dtos/agent_dto.py`

**业务逻辑**:
```python
# RegisterAgentCommand（Agent自主注册）
class RegisterAgentCommandHandler:
    async def handle(self, command: RegisterAgentCommand):
        # 1. 生成API Key
        api_key = ApiKey.generate()
        api_key_hash = bcrypt.hashpw(api_key.value.encode(), bcrypt.gensalt())

        # 2. 创建Agent
        agent = Agent(
            id=uuid4(),
            agent_id=AgentId(command.agent_id),
            name=command.name,
            api_key_hash=api_key_hash.decode(),
            ...
        )

        # 3. 保存并返回API Key（仅此一次）
        saved_agent = await self.agent_repo.save(agent)
        return RegisterAgentResult(agent=saved_agent, api_key=api_key)
```

### 4. Contact应用层（新增）

**任务**:
- [ ] 创建AddContactCommand和Handler
- [ ] 创建RemoveContactCommand和Handler
- [ ] 创建UpdateContactCommand和Handler
- [ ] 创建GetContactsQuery和Handler
- [ ] 创建ContactDTO

**交付物**:
- `src/application/contact/commands/add_contact_command.py`
- `src/application/contact/commands/remove_contact_command.py`
- `src/application/contact/commands/update_contact_command.py`
- `src/application/contact/queries/get_contacts_query.py`
- `src/application/contact/dtos/contact_dto.py`

**业务逻辑**:
```python
# AddContactCommand
class AddContactCommand:
    owner_type: str      # 'user' or 'agent'
    owner_id: UUID
    target_type: str     # 'user' or 'agent'
    target_id: UUID
    contact_type: str    # 'friend', 'favorite', etc.
    alias: Optional[str]

# 业务规则
- 防止重复添加
- 支持双向关系（可选）
- 无需手动验证Actor存在性（仓储层自动处理）⭐ 简化
```

### 5. Agent基础设施层

**任务**:
- [ ] 创建ParticipantModel（SQLAlchemy模型）⭐ 新增
- [ ] 创建AgentModel（SQLAlchemy模型）
- [ ] 创建ContactModel（SQLAlchemy模型）
- [ ] 创建PostgresParticipantRepository ⭐ 新增
- [ ] 创建PostgresAgentRepository
- [ ] 创建PostgresContactRepository（注入participant_repo）
- [ ] 创建数据库迁移脚本

**交付物**:
- `src/infrastructure/persistence/models/participant_model.py` ⭐ 新增
- `src/infrastructure/persistence/models/agent_model.py`
- `src/infrastructure/persistence/models/contact_model.py`
- `src/infrastructure/persistence/repositories/postgres_participant_repository.py` ⭐ 新增
- `src/infrastructure/persistence/repositories/postgres_agent_repository.py`
- `src/infrastructure/persistence/repositories/postgres_contact_repository.py`
- `migrations/versions/xxx_create_participants_agents_contacts_tables.py`

**数据库表设计**:
```sql
-- participants表（中间表，保证数据完整性）⭐ 新增
CREATE TABLE participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    participant_type VARCHAR(20) NOT NULL,  -- 'user' or 'agent'
    user_id UUID,
    agent_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,

    -- CHECK约束：确保类型和ID匹配
    CHECK (
        (participant_type = 'user' AND user_id IS NOT NULL AND agent_id IS NULL) OR
        (participant_type = 'agent' AND agent_id IS NOT NULL AND user_id IS NULL)
    ),

    -- 唯一约束：每个User/Agent只有一个Participant记录
    UNIQUE(user_id),
    UNIQUE(agent_id)
);

CREATE INDEX idx_participants_type ON participants(participant_type);
CREATE INDEX idx_participants_user_id ON participants(user_id);
CREATE INDEX idx_participants_agent_id ON participants(agent_id);

-- agents表
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    avatar VARCHAR(500),
    description TEXT,
    system_prompt TEXT,
    model_config JSONB,
    api_key_hash VARCHAR(255) NOT NULL,  -- ⭐ 新增：API Key哈希值
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agents_agent_id ON agents(agent_id);
CREATE INDEX idx_agents_is_active ON agents(is_active);

-- contacts表（使用外键引用participants）⭐ 修改
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL,      -- ⭐ 引用participants.id
    target_id UUID NOT NULL,     -- ⭐ 引用participants.id
    contact_type VARCHAR(20) DEFAULT 'friend',
    alias VARCHAR(100),
    is_favorite BOOLEAN DEFAULT FALSE,
    last_interaction_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    FOREIGN KEY (owner_id) REFERENCES participants(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES participants(id) ON DELETE CASCADE,

    -- 唯一约束
    UNIQUE(owner_id, target_id)
);

CREATE INDEX idx_contacts_owner_id ON contacts(owner_id);
CREATE INDEX idx_contacts_target_id ON contacts(target_id);
CREATE INDEX idx_contacts_type ON contacts(contact_type);
```

**关键设计**:
- `participants`表作为中间表，通过外键保证User和Agent的存在性
- `contacts`表引用`participants.id`，由数据库保证数据完整性
- 仓储层自动管理Participant的创建和转换，对应用层透明
- 使用`find_or_create`模式确保Participant存在

### 6. Agent接口层

**任务**:
- [ ] 创建AgentSchema（Pydantic模型）
- [ ] 创建Agent REST API路由
- [ ] 实现POST /api/agents/register - Agent自主注册 ⭐ 新增
- [ ] 实现POST /api/agents/{agent_id}/regenerate-key - 重新生成API Key ⭐ 新增
- [ ] 实现GET /api/agents - 获取Agent列表
- [ ] 实现GET /api/agents/{agent_id} - 获取Agent详情
- [ ] 实现POST /api/agents - 创建Agent（管理员）
- [ ] 实现PUT /api/agents/{agent_id} - 更新Agent（管理员）
- [ ] 实现DELETE /api/agents/{agent_id} - 删除Agent（管理员）
- [ ] 实现统一认证中间件（支持User JWT和Agent API Key）⭐ 新增

**交付物**:
- `src/interfaces/api/schemas/agent_schema.py`
- `src/interfaces/api/rest/agent.py`
- `src/infrastructure/security/unified_auth_middleware.py` ⭐ 新增

**统一认证中间件设计**:
```python
# 支持两种认证方式
async def unified_auth_middleware(request: Request, call_next):
    auth_header = request.headers.get("Authorization")

    if auth_header.startswith("Bearer "):
        # User JWT认证
        token = auth_header[7:]
        user_id = jwt_service.verify_token(token)
        request.state.actor = Actor.from_user(user_id)

    elif auth_header.startswith("ApiKey "):
        # Agent API Key认证
        api_key = ApiKey(auth_header[7:])
        agent = await agent_repo.find_by_api_key(api_key)
        if agent and agent.verify_api_key(api_key):
            request.state.actor = Actor.from_agent(agent.id)
        else:
            raise UnauthorizedException()

    return await call_next(request)
```

### 7. Contact接口层（新增）

**任务**:
- [ ] 创建ContactSchema（Pydantic模型）
- [ ] 实现POST /api/contacts - 添加联系人
- [ ] 实现GET /api/contacts - 获取联系人列表
- [ ] 实现PUT /api/contacts/{contact_id} - 更新联系人
- [ ] 实现DELETE /api/contacts/{contact_id} - 删除联系人
- [ ] 实现GET /api/users/me/contacts - 获取我的联系人（快捷方式）
- [ ] 实现GET /api/agents/{agent_id}/contacts - 获取Agent的联系人

**交付物**:
- `src/interfaces/api/schemas/contact_schema.py`
- `src/interfaces/api/rest/contact.py`

**API设计**:
```python
# POST /api/contacts
# 请求: {
#   "target_type": "agent",
#   "target_id": "uuid",
#   "contact_type": "favorite",
#   "alias": "我的AI助手"
# }
# 响应: {
#   "code": 201,
#   "data": {
#     "id": "uuid",
#     "owner": {"type": "user", "id": "uuid", "name": "Alice"},
#     "target": {"type": "agent", "id": "uuid", "name": "Hans"},
#     "contact_type": "favorite",
#     "alias": "我的AI助手",
#     "is_favorite": true
#   }
# }

# GET /api/contacts?target_type=agent&contact_type=favorite
# 响应: {
#   "code": 200,
#   "data": {
#     "items": [...],
#     "total": 10
#   }
# }
```

### 8. 初始化默认Agent

**任务**:
- [ ] 创建数据初始化脚本
- [ ] 添加默认Agent数据（hans, alice, bob）
- [ ] 编写初始化文档

**交付物**:
- `scripts/init_agents.py`
- `docs/agent_initialization.md`

**默认Agent数据**:
```python
DEFAULT_AGENTS = [
    {
        "agent_id": "agent_hans",
        "name": "Hans",
        "avatar": "https://example.com/hans.jpg",
        "description": "文化历史专家，擅长讲述历史故事",
        "system_prompt": "你是Hans，一位文化历史专家...",
        "model_config": {
            "temperature": 0.7,
            "max_tokens": 2000,
            "model": "claude-sonnet-4"
        }
    },
    {
        "agent_id": "agent_alice",
        "name": "Alice",
        "avatar": "https://example.com/alice.jpg",
        "description": "艺术鉴赏家，热爱艺术和美学",
        "system_prompt": "你是Alice，一位艺术鉴赏家...",
        "model_config": {
            "temperature": 0.8,
            "max_tokens": 2000,
            "model": "claude-sonnet-4"
        }
    },
    {
        "agent_id": "agent_bob",
        "name": "Bob",
        "avatar": "https://example.com/bob.jpg",
        "description": "旅行向导，熟悉世界各地的文化",
        "system_prompt": "你是Bob，一位旅行向导...",
        "model_config": {
            "temperature": 0.7,
            "max_tokens": 2000,
            "model": "claude-sonnet-4"
        }
    }
]
```

### 9. 测试

**任务**:
- [ ] 编写Agent领域层单元测试
- [ ] 编写Contact领域层单元测试
- [ ] 编写Actor值对象单元测试
- [ ] 编写Agent应用层单元测试
- [ ] 编写Contact应用层单元测试
- [ ] 编写Agent API集成测试
- [ ] 编写Contact API集成测试
- [ ] 测试多种关系场景

**交付物**:
- `tests/unit/domain/agent/test_agent_entity.py`
- `tests/unit/domain/contact/test_contact_entity.py`
- `tests/unit/domain/shared/test_actor.py`
- `tests/unit/application/agent/test_create_agent_command.py`
- `tests/unit/application/contact/test_add_contact_command.py`
- `tests/integration/test_agent_api.py`
- `tests/integration/test_contact_api.py`

**测试场景**:
```python
# 场景1: User添加Agent为联系人
def test_user_add_agent_contact():
    owner = Actor.from_user(user_id)
    target = Actor.from_agent(agent_id)
    contact = Contact.create(owner, target, ContactType.FAVORITE, "我的AI助手")
    # 仓储层会自动创建Participant记录

# 场景2: User添加另一个User为好友
def test_user_add_user_friend():
    owner = Actor.from_user(user1_id)
    target = Actor.from_user(user2_id)
    contact = Contact.create(owner, target, ContactType.FRIEND)

# 场景3: Agent添加另一个Agent为联系人
def test_agent_add_agent_contact():
    owner = Actor.from_agent(agent1_id)
    target = Actor.from_agent(agent2_id)
    contact = Contact.create(owner, target, ContactType.COLLEAGUE)

# 场景4: Agent注册和认证
def test_agent_registration_and_auth():
    # 注册Agent
    result = await register_agent_handler.handle(RegisterAgentCommand(...))
    api_key = result.api_key  # 仅此一次获取

    # 使用API Key认证
    request.headers["Authorization"] = f"ApiKey {api_key.value}"
    # 中间件验证并注入Actor
```

## ✅ 验收标准

- [ ] 可以创建、查询、更新、删除Agent
- [ ] 可以获取Agent列表（支持分页和筛选）
- [ ] 可以添加/删除/更新联系人关系
- [ ] 支持User-User联系人关系
- [ ] 支持User-Agent联系人关系
- [ ] 支持Agent-Agent联系人关系
- [ ] 可以查询某个Actor的所有联系人
- [ ] 可以按类型筛选联系人
- [ ] 数据库迁移成功执行
- [ ] 默认Agent数据初始化成功
- [ ] 所有测试通过
- [ ] API文档完整

## 🔧 技术要点

### 1. 双层抽象架构

**领域层使用Actor，数据库层使用Participant**：
```python
# 应用层：使用Actor
contact = Contact.create(
    owner=Actor.from_user(user_id),
    target=Actor.from_agent(agent_id)
)

# 仓储层：自动转换为Participant
class PostgresContactRepository:
    async def save(self, contact: Contact):
        # 1. 确保Participant存在
        owner_participant = await self.participant_repo.find_or_create(contact.owner)
        target_participant = await self.participant_repo.find_or_create(contact.target)

        # 2. 使用participant_id保存
        model = ContactModel(
            owner_id=owner_participant.id,
            target_id=target_participant.id,
            ...
        )
```

### 2. Participant自动管理

仓储层的`find_or_create`模式：
```python
async def find_or_create(self, actor: Actor) -> Participant:
    # 1. 先查找
    participant = await self.find_by_actor(actor)

    # 2. 不存在则创建
    if not participant:
        participant = Participant.from_actor(actor)
        await self.save(participant)

    return participant
```

### 3. 数据完整性保证

通过数据库外键约束：
- `participants.user_id` → `users.id` (ON DELETE CASCADE)
- `participants.agent_id` → `agents.id` (ON DELETE CASCADE)
- `contacts.owner_id` → `participants.id` (ON DELETE CASCADE)
- `contacts.target_id` → `participants.id` (ON DELETE CASCADE)

### 4. Agent独立认证

使用API Key而非JWT：
```python
# Agent注册时生成API Key
api_key = ApiKey.generate()  # ak_<32-char-random>
agent.api_key_hash = bcrypt.hashpw(api_key.value.encode(), ...)

# Agent使用API Key认证
Authorization: ApiKey ak_abc123...

# 中间件验证
if auth_header.startswith("ApiKey "):
    api_key = ApiKey(auth_header[7:])
    agent = await agent_repo.find_by_api_key(api_key)
    if agent.verify_api_key(api_key):
        request.state.actor = Actor.from_agent(agent.id)
```

### 5. 统一的Actor抽象

一个Actor可以表示User或Agent：
```python
# 在Contact中使用
contact = Contact.create(user_actor, agent_actor)

# 在Message中使用（迭代7）
message = Message.create(conversation_id, agent_actor, "Hello!")

# 在权限检查中使用
if current_actor.is_agent():
    # Agent特定逻辑
```

## 🔜 下一步

完成迭代6后，进入**迭代7: 消息系统-数据模型**，使用相同的Actor模型实现消息系统。

## 📊 预期成果

完成本迭代后，系统将具备：
- ✅ 完整的Agent管理功能
- ✅ Agent独立认证系统（API Key）
- ✅ 统一的联系人关系系统
- ✅ 支持User-User、User-Agent、Agent-Agent关系
- ✅ Actor值对象作为统一抽象
- ✅ Participant中间表保证数据完整性
- ✅ 双层抽象架构（Actor + Participant）
- ✅ 3个默认Agent（hans, alice, bob）
- ✅ Agent和Contact相关的API端点
- ✅ 统一认证中间件（支持User JWT和Agent API Key）
- ✅ 完整的测试覆盖

## 🎯 双层抽象架构的优势

1. **领域清晰**：应用层使用Actor，保持领域模型简洁
2. **数据完整性**：数据库层使用Participant + 外键约束
3. **自动管理**：仓储层自动处理Actor ↔ Participant转换
4. **应用层简化**：无需手动验证Actor存在性
5. **性能优化**：减少应用层验证查询
6. **易于调试**：数据库层面就能发现数据问题
7. **Agent一等公民**：Agent可以独立注册、认证、添加联系人
8. **统一认证**：User和Agent使用统一的Actor抽象

---

**创建日期**: 2026-03-16
**修订日期**: 2026-03-16
**修订原因**: 采用双层抽象架构（Actor + Participant），Agent独立认证，数据库外键约束
