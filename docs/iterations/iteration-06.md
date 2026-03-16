# 迭代6: Agent管理（方案C - 多态Actor模型）

> 实现Agent信息管理和通用的联系人关系系统

## 📋 迭代信息

- **迭代编号**: 6
- **预计时间**: 1-2天
- **当前状态**: 🟡 计划中
- **依赖迭代**: 迭代5 ✅
- **开始日期**: 待定

## 🎯 迭代目标

实现Agent实体管理和统一的联系人关系系统，支持User-User、User-Agent、Agent-Agent之间的关系建模，为后续的消息系统打下基础。

## 💡 设计理念

**方案C：多态Actor模型**

- User和Agent保持各自的领域完整性
- 使用`(actor_type, actor_id)`多态引用实现统一标识
- 无需Participant中间表，结构简洁
- 通过`contacts`表统一管理所有类型间的关系

## 📝 任务清单

### 1. Agent领域层

**任务**:
- [ ] 创建AgentId值对象
- [ ] 创建AgentConfig值对象（模型配置）
- [ ] 创建Agent实体
- [ ] 创建AgentRepository接口
- [ ] 创建Actor值对象（统一User和Agent的标识）

**交付物**:
- `src/domain/agent/value_objects/agent_id.py`
- `src/domain/agent/value_objects/agent_config.py`
- `src/domain/agent/entities/agent.py`
- `src/domain/agent/repositories/agent_repository.py`
- `src/domain/shared/value_objects/actor.py` ⭐ 新增

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
    is_active: bool
    created_by: Optional[UUID]  # 创建者的user_id
    created_at: datetime
    updated_at: datetime

    def to_actor(self) -> Actor:
        """转换为Actor。"""
        return Actor.from_agent(self.id)
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
- [ ] 创建CreateAgentCommand和Handler
- [ ] 创建UpdateAgentCommand和Handler
- [ ] 创建GetAgentQuery和Handler
- [ ] 创建ListAgentsQuery和Handler
- [ ] 创建AgentDTO

**交付物**:
- `src/application/agent/commands/create_agent_command.py`
- `src/application/agent/commands/update_agent_command.py`
- `src/application/agent/queries/get_agent_query.py`
- `src/application/agent/queries/list_agents_query.py`
- `src/application/agent/dtos/agent_dto.py`

**业务逻辑**:
- 创建Agent时自动生成agent_id（如果未提供）
- 验证agent_id的唯一性
- 验证model_config的有效性
- 支持按agent_id或UUID查询

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
- 验证owner和target都存在
- 防止重复添加
- 支持双向关系（可选）
```

### 5. Agent基础设施层

**任务**:
- [ ] 创建AgentModel（SQLAlchemy模型）
- [ ] 创建ContactModel（SQLAlchemy模型）⭐ 新增
- [ ] 创建PostgresAgentRepository
- [ ] 创建PostgresContactRepository ⭐ 新增
- [ ] 创建数据库迁移脚本

**交付物**:
- `src/infrastructure/persistence/models/agent_model.py`
- `src/infrastructure/persistence/models/contact_model.py` ⭐ 新增
- `src/infrastructure/persistence/repositories/postgres_agent_repository.py`
- `src/infrastructure/persistence/repositories/postgres_contact_repository.py` ⭐ 新增
- `migrations/versions/xxx_create_agents_contacts_tables.py`

**数据库表设计**:
```sql
-- agents表
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    avatar VARCHAR(500),
    description TEXT,
    system_prompt TEXT,
    model_config JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- contacts表（统一的联系人关系）⭐ 替代user_agents
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_type VARCHAR(20) NOT NULL,   -- 'user' or 'agent'
    owner_id UUID NOT NULL,
    target_type VARCHAR(20) NOT NULL,  -- 'user' or 'agent'
    target_id UUID NOT NULL,
    contact_type VARCHAR(20) DEFAULT 'friend',
    alias VARCHAR(100),
    is_favorite BOOLEAN DEFAULT FALSE,
    last_interaction_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(owner_type, owner_id, target_type, target_id)
);

-- 索引
CREATE INDEX idx_agents_agent_id ON agents(agent_id);
CREATE INDEX idx_agents_is_active ON agents(is_active);
CREATE INDEX idx_contacts_owner ON contacts(owner_type, owner_id);
CREATE INDEX idx_contacts_target ON contacts(target_type, target_id);
CREATE INDEX idx_contacts_type ON contacts(contact_type);
```

**关键设计**:
- `contacts`表使用多态引用，无外键约束
- 应用层负责验证owner_id和target_id的有效性
- 支持所有类型间的关系：User-User、User-Agent、Agent-Agent

### 6. Agent接口层

**任务**:
- [ ] 创建AgentSchema（Pydantic模型）
- [ ] 创建Agent REST API路由
- [ ] 实现GET /api/agents - 获取Agent列表
- [ ] 实现GET /api/agents/{agent_id} - 获取Agent详情
- [ ] 实现POST /api/agents - 创建Agent（管理员）
- [ ] 实现PUT /api/agents/{agent_id} - 更新Agent（管理员）
- [ ] 实现DELETE /api/agents/{agent_id} - 删除Agent（管理员）

**交付物**:
- `src/interfaces/api/schemas/agent_schema.py`
- `src/interfaces/api/rest/agent.py`

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

### 1. Actor值对象设计

Actor是核心抽象，统一表示User或Agent：
```python
# 使用示例
user_actor = Actor.from_user(user_id)
agent_actor = Actor.from_agent(agent_id)

# 在Contact中使用
contact = Contact.create(user_actor, agent_actor)

# 在Message中使用（迭代7）
message = Message.create(conversation_id, user_actor, "Hello!")
```

### 2. 多态引用的应用层验证

由于没有数据库外键约束，需要在应用层验证：
```python
async def validate_actor(actor: Actor) -> bool:
    if actor.is_user():
        user = await user_repo.find_by_id(actor.actor_id)
        return user is not None
    elif actor.is_agent():
        agent = await agent_repo.find_by_id(actor.actor_id)
        return agent is not None
    return False
```

### 3. Contacts表的灵活性

一张表覆盖所有关系类型：
- User收藏Agent: `owner_type='user', target_type='agent', contact_type='favorite'`
- User添加好友: `owner_type='user', target_type='user', contact_type='friend'`
- Agent认识Agent: `owner_type='agent', target_type='agent', contact_type='colleague'`

### 4. 查询优化

使用复合索引优化查询：
```sql
-- 查询某个User的所有Agent联系人
SELECT * FROM contacts
WHERE owner_type='user' AND owner_id=? AND target_type='agent';

-- 查询某个Agent的所有联系人
SELECT * FROM contacts
WHERE owner_type='agent' AND owner_id=?;
```

### 5. 权限控制

- 普通用户：只能管理自己的联系人
- Agent：可以管理自己的联系人（通过API或自动化）
- 管理员：可以创建、更新、删除Agent

## 🔜 下一步

完成迭代6后，进入**迭代7: 消息系统-数据模型**，使用相同的Actor模型实现消息系统。

## 📊 预期成果

完成本迭代后，系统将具备：
- ✅ 完整的Agent管理功能
- ✅ 统一的联系人关系系统
- ✅ 支持User-User、User-Agent、Agent-Agent关系
- ✅ Actor值对象作为统一抽象
- ✅ 3个默认Agent（hans, alice, bob）
- ✅ Agent和Contact相关的API端点
- ✅ 完整的测试覆盖

## 🎯 方案C的优势

1. **结构简洁**：无需Participant中间表
2. **关系完整**：contacts表天然覆盖所有类型间的关系
3. **领域清晰**：User和Agent各自保持领域完整性
4. **易于扩展**：未来可轻松添加新的actor_type
5. **性能良好**：减少JOIN，查询更直接

---

**创建日期**: 2026-03-16
**修订日期**: 2026-03-16
**修订原因**: 采用方案C（多态Actor模型），用contacts表替代user_agents表
