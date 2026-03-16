# 迭代6: Agent管理

> 实现Agent信息管理和用户与Agent的关联

## 📋 迭代信息

- **迭代编号**: 6
- **预计时间**: 1-2天
- **当前状态**: 🟡 计划中
- **依赖迭代**: 迭代5 ✅
- **开始日期**: 待定

## 🎯 迭代目标

实现Agent实体管理、用户与Agent的关联关系，为后续的消息系统打下基础。

## 📝 任务清单

### 1. Agent领域层

**任务**:
- [ ] 创建AgentId值对象
- [ ] 创建AgentConfig值对象（模型配置）
- [ ] 创建Agent实体
- [ ] 创建AgentRepository接口
- [ ] 创建AgentDomainService（可选）

**交付物**:
- `src/domain/agent/value_objects/agent_id.py`
- `src/domain/agent/value_objects/agent_config.py`
- `src/domain/agent/entities/agent.py`
- `src/domain/agent/repositories/agent_repository.py`

**设计要点**:
```python
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
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
```

### 2. Agent应用层

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

### 3. Agent基础设施层

**任务**:
- [ ] 创建AgentModel（SQLAlchemy模型）
- [ ] 创建UserAgentModel（关联表模型）
- [ ] 创建PostgresAgentRepository
- [ ] 创建数据库迁移脚本

**交付物**:
- `src/infrastructure/persistence/models/agent_model.py`
- `src/infrastructure/persistence/models/user_agent_model.py`
- `src/infrastructure/persistence/repositories/postgres_agent_repository.py`
- `migrations/versions/xxx_create_agents_tables.py`

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

-- user_agents表（用户与Agent的关联）
CREATE TABLE user_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    is_favorite BOOLEAN DEFAULT FALSE,
    last_interaction_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, agent_id)
);

-- 索引
CREATE INDEX idx_agents_agent_id ON agents(agent_id);
CREATE INDEX idx_agents_is_active ON agents(is_active);
CREATE INDEX idx_user_agents_user_id ON user_agents(user_id);
CREATE INDEX idx_user_agents_agent_id ON user_agents(agent_id);
```

### 4. Agent接口层

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

**API设计**:
```python
# GET /api/agents
# 响应: {
#   "code": 200,
#   "data": [
#     {
#       "id": "uuid",
#       "agent_id": "agent_hans",
#       "name": "Hans",
#       "avatar": "url",
#       "description": "...",
#       "is_active": true
#     }
#   ]
# }

# GET /api/agents/agent_hans
# 响应: {
#   "code": 200,
#   "data": {
#     "id": "uuid",
#     "agent_id": "agent_hans",
#     "name": "Hans",
#     "avatar": "url",
#     "description": "...",
#     "system_prompt": "...",
#     "model_config": {...},
#     "is_active": true
#   }
# }
```

### 5. 用户与Agent关联

**任务**:
- [ ] 创建AddUserAgentCommand和Handler
- [ ] 创建RemoveUserAgentCommand和Handler
- [ ] 创建GetUserAgentsQuery和Handler
- [ ] 实现POST /api/users/me/agents/{agent_id} - 添加Agent
- [ ] 实现DELETE /api/users/me/agents/{agent_id} - 移除Agent
- [ ] 实现GET /api/users/me/agents - 获取我的Agent列表
- [ ] 实现PUT /api/users/me/agents/{agent_id}/favorite - 设置收藏

**交付物**:
- `src/application/agent/commands/add_user_agent_command.py`
- `src/application/agent/commands/remove_user_agent_command.py`
- `src/application/agent/queries/get_user_agents_query.py`
- 更新 `src/interfaces/api/rest/user.py` 或创建新路由

### 6. 初始化默认Agent

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

### 7. 测试

**任务**:
- [ ] 编写Agent领域层单元测试
- [ ] 编写Agent应用层单元测试
- [ ] 编写Agent API集成测试
- [ ] 编写用户与Agent关联测试

**交付物**:
- `tests/unit/domain/agent/test_agent_entity.py`
- `tests/unit/application/agent/test_create_agent_command.py`
- `tests/integration/test_agent_api.py`

## ✅ 验收标准

- [ ] 可以创建、查询、更新、删除Agent
- [ ] 可以获取Agent列表（支持分页和筛选）
- [ ] 用户可以添加/移除Agent到自己的列表
- [ ] 用户可以查看自己的Agent列表
- [ ] 用户可以设置收藏的Agent
- [ ] 数据库迁移成功执行
- [ ] 默认Agent数据初始化成功
- [ ] 所有测试通过
- [ ] API文档完整

## 🔧 技术要点

### 1. AgentId设计

使用字符串格式的agent_id作为业务标识符，UUID作为数据库主键：
- agent_id: 业务层使用，便于记忆和引用（如agent_hans）
- id (UUID): 数据库主键，保证唯一性

### 2. 模型配置存储

使用JSONB字段存储model_config，支持灵活的配置：
```python
model_config = {
    "temperature": 0.7,
    "max_tokens": 2000,
    "model": "claude-sonnet-4",
    "top_p": 0.9,
    "frequency_penalty": 0.0
}
```

### 3. 用户与Agent关联

使用中间表user_agents管理多对多关系：
- 支持用户添加多个Agent
- 支持Agent被多个用户使用
- 记录最后交互时间
- 支持收藏功能

### 4. 权限控制

- 普通用户：只能查看和使用Agent
- 管理员：可以创建、更新、删除Agent
- 使用依赖注入验证用户权限

## 🔜 下一步

完成迭代6后，进入**迭代7: 消息系统-数据模型**

## 📊 预期成果

完成本迭代后，系统将具备：
- ✅ 完整的Agent管理功能
- ✅ 用户与Agent的关联关系
- ✅ 3个默认Agent（hans, alice, bob）
- ✅ Agent相关的API端点
- ✅ 完整的测试覆盖

---

**创建日期**: 2026-03-16
