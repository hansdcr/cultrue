# Agent独立认证机制设计（方案B）

> 本文档补充说明迭代6中Agent独立认证的设计细节

## 📋 概述

为了让Agent成为真正的一等公民，具备与User相同的能力（注册、登录、添加好友、创建会话等），我们采用**方案B：Agent独立认证**。

## 🎯 设计目标

- Agent可以注册并获得API Key
- Agent可以使用API Key调用所有API
- Agent可以主动发起会话、发送消息、管理contacts
- User和Agent在API层面完全平等
- 保持User和Agent领域的清晰分离

## 🏗️ 架构设计

### 认证流程对比

**User认证流程**：
```
1. User注册 → 创建User记录（含password_hash）
2. User登录 → 验证密码 → 生成JWT Token
3. User调用API → 携带Bearer Token → 中间件验证 → 提取user_id
4. 业务逻辑 → 使用Actor.from_user(user_id)
```

**Agent认证流程**：
```
1. Agent注册 → 创建Agent记录（含api_key_hash）→ 返回API Key
2. Agent认证 → 验证API Key → 生成JWT Token（可选）或直接使用API Key
3. Agent调用API → 携带ApiKey Token → 中间件验证 → 提取agent_id
4. 业务逻辑 → 使用Actor.from_agent(agent_id)
```

### 统一认证中间件

```python
async def auth_middleware(request: Request):
    """统一认证中间件，支持User和Agent。"""
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise UnauthorizedException("Missing authorization header")

    if auth_header.startswith("Bearer "):
        # User JWT Token
        token = auth_header[7:]
        payload = verify_jwt_token(token)
        user_id = UUID(payload["sub"])
        request.state.actor = Actor.from_user(user_id)
        request.state.actor_entity_id = user_id

    elif auth_header.startswith("ApiKey "):
        # Agent API Key
        api_key = auth_header[7:]
        agent = await verify_agent_api_key(api_key)
        request.state.actor = Actor.from_agent(agent.id)
        request.state.actor_entity_id = agent.id

    else:
        raise UnauthorizedException("Invalid authorization header format")
```

## 📦 领域层设计

### 1. ApiKey值对象

```python
# src/domain/agent/value_objects/api_key.py

import secrets
from dataclasses import dataclass

@dataclass(frozen=True)
class ApiKey:
    """API Key值对象。

    格式: ak_<32字符随机字符串>
    示例: ak_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
    """
    value: str

    @classmethod
    def generate(cls) -> "ApiKey":
        """生成新的API Key。"""
        random_part = secrets.token_urlsafe(24)  # 生成32字符
        return cls(value=f"ak_{random_part}")

    def __str__(self) -> str:
        return self.value

    def mask(self) -> str:
        """返回掩码版本，用于显示。"""
        if len(self.value) < 12:
            return "ak_***"
        return f"{self.value[:6]}...{self.value[-4:]}"
```

### 2. Agent实体更新

```python
# src/domain/agent/entities/agent.py

class Agent:
    """Agent实体。"""
    id: UUID
    agent_id: AgentId
    name: str
    avatar: Optional[str]
    description: Optional[str]
    system_prompt: Optional[str]
    model_config: AgentConfig
    api_key_hash: str  # ⭐ 新增：API Key的hash
    is_active: bool
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    def verify_api_key(self, api_key: ApiKey, hasher: "PasswordHasher") -> bool:
        """验证API Key。"""
        return hasher.verify(api_key.value, self.api_key_hash)

    def regenerate_api_key(self, hasher: "PasswordHasher") -> ApiKey:
        """重新生成API Key。"""
        new_api_key = ApiKey.generate()
        self.api_key_hash = hasher.hash(new_api_key.value)
        self.updated_at = datetime.now(timezone.utc)
        return new_api_key

    def to_actor(self) -> Actor:
        """转换为Actor。"""
        return Actor.from_agent(self.id)
```

### 3. Agent认证服务接口

```python
# src/domain/agent/services/agent_auth_service.py

from abc import ABC, abstractmethod

class AgentAuthService(ABC):
    """Agent认证服务接口。"""

    @abstractmethod
    async def authenticate(self, api_key: ApiKey) -> Optional[Agent]:
        """通过API Key认证Agent。"""
        pass

    @abstractmethod
    async def generate_api_key(self, agent: Agent) -> ApiKey:
        """为Agent生成新的API Key。"""
        pass
```

## 📦 应用层设计

### 1. RegisterAgentCommand

```python
# src/application/agent/commands/register_agent_command.py

@dataclass
class RegisterAgentCommand:
    """注册Agent命令。"""
    agent_id: str  # 如：agent_hans
    name: str
    avatar: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_config: Optional[dict] = None
    created_by: Optional[UUID] = None  # 创建者user_id（可选）

@dataclass
class RegisterAgentResult:
    """注册结果。"""
    agent: Agent
    api_key: ApiKey  # ⭐ 返回明文API Key（仅此一次）

class RegisterAgentCommandHandler:
    """注册Agent命令处理器。"""

    def __init__(
        self,
        agent_repository: AgentRepository,
        password_hasher: PasswordHasher
    ):
        self.agent_repository = agent_repository
        self.password_hasher = password_hasher

    async def handle(self, command: RegisterAgentCommand) -> RegisterAgentResult:
        # 1. 验证agent_id唯一性
        existing = await self.agent_repository.find_by_agent_id(command.agent_id)
        if existing:
            raise ValidationException(f"Agent ID '{command.agent_id}' already exists")

        # 2. 生成API Key
        api_key = ApiKey.generate()
        api_key_hash = self.password_hasher.hash(api_key.value)

        # 3. 创建Agent实体
        agent = Agent(
            id=uuid4(),
            agent_id=AgentId(command.agent_id),
            name=command.name,
            avatar=command.avatar,
            description=command.description,
            system_prompt=command.system_prompt,
            model_config=AgentConfig(**(command.model_config or {})),
            api_key_hash=api_key_hash,
            is_active=True,
            created_by=command.created_by,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # 4. 保存
        saved_agent = await self.agent_repository.save(agent)

        return RegisterAgentResult(agent=saved_agent, api_key=api_key)
```

### 2. AuthenticateAgentCommand

```python
# src/application/agent/commands/authenticate_agent_command.py

@dataclass
class AuthenticateAgentCommand:
    """Agent认证命令。"""
    api_key: str

@dataclass
class AuthenticateAgentResult:
    """认证结果。"""
    agent: Agent
    actor: Actor

class AuthenticateAgentCommandHandler:
    """Agent认证命令处理器。"""

    def __init__(
        self,
        agent_repository: AgentRepository,
        password_hasher: PasswordHasher
    ):
        self.agent_repository = agent_repository
        self.password_hasher = password_hasher

    async def handle(self, command: AuthenticateAgentCommand) -> AuthenticateAgentResult:
        # 1. 解析API Key
        if not command.api_key.startswith("ak_"):
            raise AuthenticationException("Invalid API Key format")

        api_key = ApiKey(command.api_key)

        # 2. 查找所有active的Agent（需要遍历验证）
        # 注意：这里可以优化，比如在api_key_hash上建立索引
        agents = await self.agent_repository.find_all(is_active=True)

        for agent in agents:
            if agent.verify_api_key(api_key, self.password_hasher):
                return AuthenticateAgentResult(
                    agent=agent,
                    actor=agent.to_actor()
                )

        raise AuthenticationException("Invalid API Key")
```

### 3. RegenerateApiKeyCommand

```python
# src/application/agent/commands/regenerate_api_key_command.py

@dataclass
class RegenerateApiKeyCommand:
    """重新生成API Key命令。"""
    agent_id: UUID

@dataclass
class RegenerateApiKeyResult:
    """重新生成结果。"""
    agent: Agent
    new_api_key: ApiKey

class RegenerateApiKeyCommandHandler:
    """重新生成API Key命令处理器。"""

    def __init__(
        self,
        agent_repository: AgentRepository,
        password_hasher: PasswordHasher
    ):
        self.agent_repository = agent_repository
        self.password_hasher = password_hasher

    async def handle(self, command: RegenerateApiKeyCommand) -> RegenerateApiKeyResult:
        # 1. 查找Agent
        agent = await self.agent_repository.find_by_id(command.agent_id)
        if not agent:
            raise NotFoundException("Agent not found")

        # 2. 重新生成API Key
        new_api_key = agent.regenerate_api_key(self.password_hasher)

        # 3. 保存
        updated_agent = await self.agent_repository.update(agent)

        return RegenerateApiKeyResult(
            agent=updated_agent,
            new_api_key=new_api_key
        )
```

## 📦 基础设施层设计

### 1. 数据库表更新

```sql
-- agents表添加api_key_hash字段
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    avatar VARCHAR(500),
    description TEXT,
    system_prompt TEXT,
    model_config JSONB,
    api_key_hash VARCHAR(255) NOT NULL,  -- ⭐ 新增
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_agents_agent_id ON agents(agent_id);
CREATE INDEX idx_agents_is_active ON agents(is_active);
CREATE INDEX idx_agents_api_key_hash ON agents(api_key_hash);  -- ⭐ 新增（优化认证查询）
```

### 2. ApiKeyService

```python
# src/infrastructure/security/api_key_service.py

class ApiKeyService:
    """API Key服务。"""

    def __init__(self, agent_repository: AgentRepository, password_hasher: PasswordHasher):
        self.agent_repository = agent_repository
        self.password_hasher = password_hasher

    async def verify_api_key(self, api_key_str: str) -> Optional[Agent]:
        """验证API Key并返回对应的Agent。"""
        if not api_key_str.startswith("ak_"):
            return None

        api_key = ApiKey(api_key_str)

        # 查找所有active的Agent
        agents = await self.agent_repository.find_all(is_active=True)

        for agent in agents:
            if agent.verify_api_key(api_key, self.password_hasher):
                return agent

        return None
```

### 3. 认证中间件更新

```python
# src/infrastructure/security/auth_middleware.py

from src.domain.shared.value_objects.actor import Actor

class AuthMiddleware:
    """统一认证中间件。"""

    def __init__(
        self,
        jwt_service: JWTService,
        api_key_service: ApiKeyService
    ):
        self.jwt_service = jwt_service
        self.api_key_service = api_key_service

    async def __call__(self, request: Request, call_next):
        # 跳过不需要认证的路径
        if request.url.path in ["/api/auth/register", "/api/auth/login", "/api/agents/register"]:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"code": 401, "message": "Missing authorization header"}
            )

        try:
            if auth_header.startswith("Bearer "):
                # User JWT Token
                token = auth_header[7:]
                payload = self.jwt_service.verify_token(token)
                user_id = UUID(payload["sub"])
                request.state.actor = Actor.from_user(user_id)
                request.state.actor_entity_id = user_id
                request.state.auth_type = "user"

            elif auth_header.startswith("ApiKey "):
                # Agent API Key
                api_key = auth_header[7:]
                agent = await self.api_key_service.verify_api_key(api_key)

                if not agent:
                    return JSONResponse(
                        status_code=401,
                        content={"code": 401, "message": "Invalid API Key"}
                    )

                request.state.actor = Actor.from_agent(agent.id)
                request.state.actor_entity_id = agent.id
                request.state.auth_type = "agent"

            else:
                return JSONResponse(
                    status_code=401,
                    content={"code": 401, "message": "Invalid authorization header format"}
                )

        except Exception as e:
            return JSONResponse(
                status_code=401,
                content={"code": 401, "message": f"Authentication failed: {str(e)}"}
            )

        return await call_next(request)
```

## 📦 接口层设计

### 1. Agent注册API

```python
# src/interfaces/api/rest/agent.py

@router.post("/api/agents/register", status_code=201)
async def register_agent(
    request: RegisterAgentRequest,
    handler: RegisterAgentCommandHandler = Depends(get_register_agent_handler)
) -> ApiResponse:
    """注册Agent。

    ⚠️ 重要：API Key仅在注册时返回一次，请妥善保存！
    """
    command = RegisterAgentCommand(
        agent_id=request.agent_id,
        name=request.name,
        avatar=request.avatar,
        description=request.description,
        system_prompt=request.system_prompt,
        model_config=request.model_config
    )

    result = await handler.handle(command)

    return ApiResponse(
        code=201,
        message="Agent registered successfully",
        data={
            "agent": AgentDTO.from_entity(result.agent).dict(),
            "api_key": result.api_key.value,  # ⭐ 明文返回（仅此一次）
            "warning": "Please save this API Key securely. It will not be shown again."
        }
    )
```

### 2. Agent认证API（可选）

```python
@router.post("/api/agents/authenticate")
async def authenticate_agent(
    request: AuthenticateAgentRequest,
    handler: AuthenticateAgentCommandHandler = Depends(get_authenticate_agent_handler)
) -> ApiResponse:
    """Agent认证（验证API Key是否有效）。"""
    command = AuthenticateAgentCommand(api_key=request.api_key)

    result = await handler.handle(command)

    return ApiResponse(
        code=200,
        message="Authentication successful",
        data={
            "agent": AgentDTO.from_entity(result.agent).dict(),
            "actor": {
                "actor_type": result.actor.actor_type.value,
                "actor_id": str(result.actor.actor_id)
            }
        }
    )
```

### 3. 重新生成API Key

```python
@router.post("/api/agents/me/regenerate-api-key")
async def regenerate_api_key(
    request: Request,
    handler: RegenerateApiKeyCommandHandler = Depends(get_regenerate_api_key_handler)
) -> ApiResponse:
    """重新生成API Key。

    ⚠️ 重要：旧的API Key将立即失效！
    """
    # 从认证中间件获取当前Agent
    if request.state.auth_type != "agent":
        raise ForbiddenException("Only agents can regenerate API keys")

    agent_id = request.state.actor_entity_id

    command = RegenerateApiKeyCommand(agent_id=agent_id)
    result = await handler.handle(command)

    return ApiResponse(
        code=200,
        message="API Key regenerated successfully",
        data={
            "new_api_key": result.new_api_key.value,
            "warning": "Please save this API Key securely. The old key is now invalid."
        }
    )
```

### 4. 获取当前Actor依赖

```python
# src/interfaces/api/dependencies.py

async def get_current_actor(request: Request) -> Actor:
    """获取当前认证的Actor（User或Agent）。"""
    if not hasattr(request.state, "actor"):
        raise UnauthorizedException("Not authenticated")
    return request.state.actor

async def get_current_user_actor(request: Request) -> Actor:
    """获取当前User Actor（仅User）。"""
    actor = await get_current_actor(request)
    if not actor.is_user():
        raise ForbiddenException("This endpoint is only for users")
    return actor

async def get_current_agent_actor(request: Request) -> Actor:
    """获取当前Agent Actor（仅Agent）。"""
    actor = await get_current_actor(request)
    if not actor.is_agent():
        raise ForbiddenException("This endpoint is only for agents")
    return actor
```

## 📦 使用示例

### Agent注册和使用流程

```bash
# 1. 注册Agent
curl -X POST http://localhost:8000/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_hans",
    "name": "Hans",
    "description": "German culture expert",
    "system_prompt": "You are Hans..."
  }'

# 响应
{
  "code": 201,
  "message": "Agent registered successfully",
  "data": {
    "agent": {
      "id": "uuid",
      "agent_id": "agent_hans",
      "name": "Hans",
      ...
    },
    "api_key": "ak_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p",
    "warning": "Please save this API Key securely. It will not be shown again."
  }
}

# 2. Agent使用API Key添加联系人
curl -X POST http://localhost:8000/api/contacts \
  -H "Authorization: ApiKey ak_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p" \
  -H "Content-Type: application/json" \
  -d '{
    "target_type": "user",
    "target_id": "user-uuid",
    "contact_type": "friend"
  }'

# 3. Agent创建会话
curl -X POST http://localhost:8000/api/conversations \
  -H "Authorization: ApiKey ak_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_type": "direct",
    "members": [
      {"actor_type": "agent", "actor_id": "agent-uuid"},
      {"actor_type": "user", "actor_id": "user-uuid"}
    ]
  }'

# 4. Agent发送消息
curl -X POST http://localhost:8000/api/conversations/{conversation_id}/messages \
  -H "Authorization: ApiKey ak_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello! I am Hans."
  }'
```

## ✅ Agent作为一等公民的能力清单

完成Agent独立认证后，Agent将具备以下能力：

- ✅ 注册账户（获得API Key）
- ✅ 认证（使用API Key调用API）
- ✅ 添加联系人（User或Agent）
- ✅ 删除联系人
- ✅ 屏蔽联系人
- ✅ 创建会话（与User或Agent）
- ✅ 发送消息
- ✅ 接收消息
- ✅ 创建群聊
- ✅ 退出群聊
- ✅ 管理自己的信息
- ✅ 重新生成API Key

**与User的唯一区别**：
- User使用username/password登录，获得JWT Token
- Agent使用API Key认证，直接使用API Key或获得JWT Token
- User有邮箱、钱包等人类特有属性
- Agent有system_prompt、model_config等AI特有属性

**在消息系统和联系人系统中，User和Agent完全平等！**

## 🔒 安全考虑

1. **API Key存储**：
   - 数据库只存储hash，不存储明文
   - 使用bcrypt或argon2进行hash
   - API Key仅在注册时返回一次

2. **API Key格式**：
   - 前缀`ak_`便于识别
   - 32字符随机字符串，足够安全
   - 使用`secrets.token_urlsafe()`生成

3. **API Key验证**：
   - 需要遍历所有Agent验证（性能考虑）
   - 可以在api_key_hash上建立索引优化
   - 或者使用缓存机制

4. **API Key重新生成**：
   - 旧Key立即失效
   - 需要Agent自己调用（需要当前有效的API Key）
   - 管理员也可以强制重新生成

## 📊 迭代6更新清单

在原有迭代6的基础上，需要添加以下内容：

### 领域层
- [ ] ApiKey值对象
- [ ] Agent实体添加api_key_hash字段
- [ ] Agent实体添加verify_api_key和regenerate_api_key方法

### 应用层
- [ ] RegisterAgentCommand和Handler
- [ ] AuthenticateAgentCommand和Handler
- [ ] RegenerateApiKeyCommand和Handler

### 基础设施层
- [ ] agents表添加api_key_hash字段
- [ ] ApiKeyService
- [ ] 更新AuthMiddleware支持ApiKey认证

### 接口层
- [ ] POST /api/agents/register
- [ ] POST /api/agents/authenticate（可选）
- [ ] POST /api/agents/me/regenerate-api-key
- [ ] 更新依赖注入：get_current_actor, get_current_user_actor, get_current_agent_actor

### 测试
- [ ] ApiKey值对象单元测试
- [ ] Agent认证单元测试
- [ ] Agent注册API集成测试
- [ ] Agent使用API Key调用API的集成测试

---

**创建日期**: 2026-03-16
**相关迭代**: 迭代6
**设计方案**: 方案B - Agent独立认证
