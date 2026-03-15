# Cultrue 后端开发计划

## Context（背景）

Cultrue是一个多工程协作项目的核心后端服务，负责用户管理、鉴权、地图功能等核心业务。它需要为以下两个项目提供API支持：

1. **agent项目**（AI智能体）- 已使用FastAPI + PostgreSQL + DDD架构实现，提供聊天、会话管理、记忆系统
2. **web-app项目**（前端应用）- React + Vite实现，包含首页、聊天、发现、联系人等5个主要页面

当前问题：
- web-app硬编码了user_id='user_001'，缺少真实的用户认证系统
- agent项目需要从cultrue获取用户和Agent的身份信息
- 缺少统一的鉴权机制和用户管理系统
- 需要地图功能支持首页的文化地图展示
- 需要设置管理功能

## 项目需求分析

### 核心通信需求（重要更新）

系统需要支持以下通信场景：
1. ✅ **User ↔ User** - 人类之间的聊天
2. ✅ **User ↔ Agent** - 人类与AI智能体的聊天
3. ✅ **Agent ↔ Agent** - AI智能体之间的聊天
4. ✅ **Agent主动发起** - Agent可以主动给User或其他Agent发送消息

> **详细设计请参考**：[消息系统设计文档](./messaging_system_design.md)

### 从web-app分析出的需求

**已实现的API调用**：
- `GET /api/chat/sessions?user_id={userId}&agent_id={agentId}` - 获取会话列表
- `GET /api/chat/history/{sessionId}` - 获取聊天历史
- `POST /api/chat` - 发送消息

**缺失的功能**：
- 用户认证/登录（当前硬编码user_id）
- 用户信息获取（个人菜单中的邮箱、账户信息）
- 钱包/积分系统
- 好友管理（添加/删除/搜索）
- 群组/发现功能
- 设置管理

### 从agent分析出的需求

**数据库表结构**：
- conversations表：{session_id, user_id, agent_id, messages(JSONB), created_at, updated_at}
- memories表：{session_id, user_id, memory_type, content, importance}

**需要cultrue提供**：
- 用户身份验证（获取有效的user_id）
- Agent信息查询（获取agent_id和配置）
- 用户与Agent的关联关系管理

## DDD架构设计

采用四层DDD架构（参考agent项目的成功实践）：

> **注意**：消息系统（Messaging）领域的详细设计请参考 [消息系统设计文档](./messaging_system_design.md)

```
src/
├── domain/                    # 领域层（业务逻辑核心）
│   ├── user/                 # 用户领域
│   │   ├── entities/         # User实体
│   │   ├── value_objects/    # Email, Password, UserId
│   │   ├── repositories/     # UserRepository接口
│   │   └── services/         # UserDomainService
│   ├── auth/                 # 鉴权领域
│   │   ├── entities/         # Token, Session
│   │   ├── value_objects/    # Credentials
│   │   ├── repositories/     # TokenRepository接口
│   │   └── services/         # AuthService接口
│   ├── agent/                # Agent领域
│   │   ├── entities/         # Agent实体
│   │   ├── value_objects/    # AgentId, AgentConfig
│   │   ├── repositories/     # AgentRepository接口
│   │   └── services/         # AgentDomainService
│   ├── messaging/            # 消息领域（新增）⭐
│   │   ├── entities/         # Conversation, Message, Participant
│   │   ├── value_objects/    # ConversationId, MessageId, ParticipantInfo
│   │   ├── repositories/     # ConversationRepository, MessageRepository
│   │   └── services/         # ConversationService, MessageService
│   └── map/                  # 地图领域
│       ├── entities/         # Location, MapPoint
│       ├── value_objects/    # Coordinates, Address
│       ├── repositories/     # LocationRepository接口
│       └── services/         # MapService接口
├── application/              # 应用层（业务用例）
│   ├── user/
│   │   ├── commands/         # CreateUserCommand, UpdateUserCommand
│   │   ├── queries/          # GetUserQuery, ListUsersQuery
│   │   └── dtos/             # UserDTO, CreateUserDTO
│   ├── auth/
│   │   ├── commands/         # LoginCommand, LogoutCommand
│   │   └── dtos/             # LoginDTO, TokenDTO
│   ├── agent/
│   │   ├── commands/         # CreateAgentCommand
│   │   ├── queries/          # GetAgentQuery
│   │   └── dtos/             # AgentDTO
│   ├── messaging/            # 消息应用层（新增）⭐
│   │   ├── commands/         # SendMessageCommand, CreateConversationCommand
│   │   ├── queries/          # GetMessagesQuery, GetConversationsQuery
│   │   └── dtos/             # MessageDTO, ConversationDTO
│   └── map/
│       ├── commands/         # CreateLocationCommand
│       ├── queries/          # SearchLocationQuery
│       └── dtos/             # LocationDTO
├── infrastructure/           # 基础设施层（技术实现）
│   ├── persistence/
│   │   ├── models/           # SQLAlchemy模型
│   │   │   ├── user_model.py
│   │   │   ├── agent_model.py
│   │   │   ├── session_model.py
│   │   │   ├── conversation_model.py  # 新增⭐
│   │   │   ├── message_model.py       # 新增⭐
│   │   │   └── location_model.py
│   │   ├── repositories/     # 仓储实现
│   │   │   ├── postgres_user_repository.py
│   │   │   ├── postgres_agent_repository.py
│   │   │   ├── postgres_conversation_repository.py  # 新增⭐
│   │   │   ├── postgres_message_repository.py       # 新增⭐
│   │   │   └── postgres_location_repository.py
│   │   └── database.py       # 数据库连接
│   ├── security/
│   │   ├── jwt_service.py    # JWT Token生成/验证
│   │   ├── password_hasher.py # 密码加密
│   │   └── auth_middleware.py # 认证中间件
│   ├── messaging/            # 消息基础设施（新增）⭐
│   │   ├── websocket/
│   │   │   ├── connection_manager.py
│   │   │   └── message_broadcaster.py
│   │   └── tasks/
│   │       ├── agent_message_scheduler.py
│   │       └── trigger_processor.py
│   └── external/
│       └── map/
│           └── map_api_service.py  # 地图API集成
└── interfaces/               # 接口层（外部交互）
    └── api/
        ├── rest/             # REST路由
        │   ├── user.py
        │   ├── auth.py
        │   ├── agent.py
        │   ├── messaging.py  # 新增⭐
        │   └── map.py
        ├── websocket/        # WebSocket端点（新增）⭐
        │   └── chat_ws.py
        ├── schemas/          # Pydantic模型
        │   ├── user_schema.py
        │   ├── auth_schema.py
        │   ├── agent_schema.py
        │   ├── messaging_schema.py  # 新增⭐
        │   └── map_schema.py
        └── dependencies.py   # FastAPI依赖注入
```

## 数据库设计

> **注意**：消息系统相关的表（conversations, conversation_participants, messages, message_read_status, agent_triggers）的详细设计请参考 [消息系统设计文档](./messaging_system_design.md)

### users表
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    avatar_url VARCHAR(500),
    bio TEXT,
    wallet_balance DECIMAL(10, 2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
```

### agents表
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) UNIQUE NOT NULL,  -- 'agent_hans', 'agent_alice'
    name VARCHAR(100) NOT NULL,
    avatar VARCHAR(500),
    description TEXT,
    system_prompt TEXT,
    model_config JSONB,  -- {temperature, max_tokens, etc}
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_agents_agent_id ON agents(agent_id);
```

### user_agents表（用户与Agent的关联）
```sql
CREATE TABLE user_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    is_favorite BOOLEAN DEFAULT FALSE,
    last_interaction_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, agent_id)
);
CREATE INDEX idx_user_agents_user_id ON user_agents(user_id);
CREATE INDEX idx_user_agents_agent_id ON user_agents(agent_id);
```

### sessions表（用户会话）
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    refresh_token_hash VARCHAR(255),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token_hash ON sessions(token_hash);
```

### locations表（地图位置）
```sql
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    address TEXT,
    category VARCHAR(50),  -- 'cultural_site', 'museum', 'landmark'
    metadata JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_locations_coordinates ON locations(latitude, longitude);
CREATE INDEX idx_locations_category ON locations(category);
```

### user_settings表
```sql
CREATE TABLE user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    language VARCHAR(10) DEFAULT 'zh-CN',
    theme VARCHAR(20) DEFAULT 'light',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    preferences JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_user_settings_user_id ON user_settings(user_id);
```

## 核心功能模块

### 1. 鉴权系统

**JWT Token方案**：
- Access Token（15分钟有效期）
- Refresh Token（7天有效期）
- Token存储在sessions表中

**认证流程**：
```
1. 用户登录 → 验证用户名/密码
2. 生成Access Token + Refresh Token
3. 保存session到数据库
4. 返回tokens给客户端
5. 客户端在请求头中携带: Authorization: Bearer <token>
6. 中间件验证token → 注入user_id到request.state
```

**关键文件**：
- `src/infrastructure/security/jwt_service.py` - Token生成/验证
- `src/infrastructure/security/auth_middleware.py` - 认证中间件
- `src/interfaces/api/rest/auth.py` - 登录/登出/刷新token接口

### 2. 用户管理

**API端点**：
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `POST /api/auth/refresh` - 刷新token
- `GET /api/users/me` - 获取当前用户信息
- `PUT /api/users/me` - 更新当前用户信息
- `GET /api/users/{user_id}` - 获取用户信息（需要权限）
- `GET /api/users/me/settings` - 获取用户设置
- `PUT /api/users/me/settings` - 更新用户设置

### 3. Agent管理

**API端点**：
- `GET /api/agents` - 获取Agent列表
- `GET /api/agents/{agent_id}` - 获取Agent详情
- `POST /api/agents` - 创建Agent（管理员）
- `PUT /api/agents/{agent_id}` - 更新Agent（管理员）
- `GET /api/users/me/agents` - 获取我的Agent列表
- `POST /api/users/me/agents/{agent_id}` - 添加Agent到我的列表
- `DELETE /api/users/me/agents/{agent_id}` - 从我的列表移除Agent

### 4. 地图功能

**API端点**：
- `GET /api/locations` - 获取位置列表（支持分页、筛选）
- `GET /api/locations/{location_id}` - 获取位置详情
- `POST /api/locations` - 创建位置
- `PUT /api/locations/{location_id}` - 更新位置
- `DELETE /api/locations/{location_id}` - 删除位置
- `GET /api/locations/nearby` - 获取附近的位置（基于经纬度）
- `GET /api/locations/search` - 搜索位置

### 5. 与Agent项目的集成接口

**代理转发**：
- `POST /api/chat` → 转发到agent服务
- `GET /api/chat/sessions` → 转发到agent服务
- `GET /api/chat/history/{session_id}` → 转发到agent服务
- `POST /api/stream` → 转发到agent服务（SSE）

**认证注入**：
- cultrue验证token后，将user_id注入到转发请求中
- 确保agent服务收到的请求都是已认证的

## 技术栈

- **Web框架**: FastAPI 0.115+
- **数据库**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0 + Alembic
- **认证**: PyJWT + passlib[bcrypt]
- **异步**: asyncio + asyncpg
- **验证**: Pydantic 2.0
- **HTTP客户端**: httpx（用于转发到agent服务）
- **WebSocket**: websockets 12.0+（实时通信）⭐
- **消息队列**: Redis 5.0+ + Celery 5.3+（异步任务）⭐
- **任务调度**: APScheduler 3.10+（定时任务）⭐
- **环境管理**: uv
- **Python版本**: 3.12

## 依赖包清单

```toml
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.13.0",
    "asyncpg>=0.29.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "pyjwt>=2.8.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.6",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
    # 消息系统新增依赖 ⭐
    "websockets>=12.0",
    "redis>=5.0.0",
    "celery>=5.3.0",
    "apscheduler>=3.10.0",
    "aioredis>=2.0.0",
]
```

## 迭代计划

> **重要更新**：由于新增了消息系统需求，迭代计划已调整。消息系统的详细实现计划请参考 [消息系统设计文档](./messaging_system_design.md)

### 第一阶段：基础架构搭建（1-2天）

**目标**：搭建DDD项目结构，配置数据库，实现基础鉴权

**任务**：
1. 创建DDD目录结构
2. 配置pyproject.toml依赖
3. 配置数据库连接（SQLAlchemy + asyncpg）
4. 创建Alembic迁移配置
5. 实现JWT Token服务
6. 实现密码加密服务
7. 创建认证中间件
8. 配置环境变量（.env.example）

**交付物**：
- 完整的项目目录结构
- 数据库连接配置
- JWT认证基础设施
- 环境配置文件

### 第二阶段：用户管理模块（2-3天）

**目标**：实现用户注册、登录、信息管理

**任务**：
1. 创建users表迁移脚本
2. 实现User实体和值对象
3. 实现UserRepository接口和实现
4. 实现用户注册Command
5. 实现用户登录Command
6. 实现用户信息查询Query
7. 创建用户相关API端点
8. 编写单元测试

**交付物**：
- 用户注册/登录API
- 用户信息管理API
- 数据库迁移脚本
- 单元测试

### 第三阶段：Agent管理模块（1-2天）

**目标**：实现Agent信息管理和用户关联

**任务**：
1. 创建agents和user_agents表迁移脚本
2. 实现Agent实体和值对象
3. 实现AgentRepository接口和实现
4. 实现Agent CRUD Commands/Queries
5. 创建Agent相关API端点
6. 初始化默认Agent数据（hans, alice, bob）
7. 编写单元测试

**交付物**：
- Agent管理API
- 用户与Agent关联API
- 默认Agent数据
- 单元测试

### 第四阶段：与Agent项目集成（1-2天）

**目标**：实现API代理转发，打通前后端

**任务**：
1. 实现HTTP客户端服务（httpx）
2. 实现聊天API代理转发
3. 实现会话API代理转发
4. 实现SSE流式响应代理
5. 在转发请求中注入认证信息
6. 配置CORS
7. 端到端测试

**交付物**：
- 聊天API代理
- 认证信息注入
- CORS配置
- 端到端测试

### 第五阶段：地图功能模块（2-3天）

**目标**：实现地图位置管理

**任务**：
1. 创建locations表迁移脚本
2. 实现Location实体和值对象
3. 实现LocationRepository接口和实现
4. 实现位置CRUD Commands/Queries
5. 实现附近位置查询（基于经纬度）
6. 实现位置搜索功能
7. 创建地图相关API端点
8. 集成第三方地图API（可选）
9. 编写单元测试

**交付物**：
- 地图位置管理API
- 位置搜索和查询API
- 单元测试

### 第六阶段：设置管理和完善（1-2天）

**目标**：实现用户设置管理，完善系统

**任务**：
1. 创建user_settings表迁移脚本
2. 实现用户设置CRUD
3. 创建设置相关API端点
4. 完善API文档（OpenAPI）
5. 添加日志系统
6. 添加错误处理
7. 性能优化
8. 安全加固

**交付物**：
- 用户设置API
- 完整的API文档
- 日志系统
- 错误处理机制

### 第七阶段：消息系统 - 基础功能（3-4天）⭐

**目标**：实现支持多方通信的消息系统基础功能

**任务**：
1. 创建消息系统数据库表（conversations, conversation_participants, messages, message_read_status）
2. 实现Messaging领域层（实体、值对象、仓储接口）
3. 实现应用层（Commands、Queries、DTOs）
4. 实现基础设施层（PostgreSQL仓储实现）
5. 实现REST API端点（会话和消息CRUD）
6. 编写单元测试

**交付物**：
- 完整的消息数据模型
- 会话和消息管理API
- 支持User-User、User-Agent、Agent-Agent通信

### 第八阶段：消息系统 - WebSocket实时通信（2-3天）⭐

**目标**：实现WebSocket实时消息推送

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

### 第九阶段：消息系统 - Agent主动消息（2-3天）⭐

**目标**：实现Agent主动发起消息的能力

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

### 第十阶段：消息系统 - 优化和完善（1-2天）⭐

**目标**：优化消息系统性能和用户体验

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

## 关键文件路径

**配置文件**：
- `/Users/gelin/Desktop/store/dev/python/ai/cultrue/pyproject.toml` - 项目配置
- `/Users/gelin/Desktop/store/dev/python/ai/cultrue/.env.example` - 环境变量模板
- `/Users/gelin/Desktop/store/dev/python/ai/cultrue/alembic.ini` - 数据库迁移配置

**入口文件**：
- `/Users/gelin/Desktop/store/dev/python/ai/cultrue/main.py` - FastAPI应用入口

**核心模块**：
- `/Users/gelin/Desktop/store/dev/python/ai/cultrue/src/domain/` - 领域层
- `/Users/gelin/Desktop/store/dev/python/ai/cultrue/src/application/` - 应用层
- `/Users/gelin/Desktop/store/dev/python/ai/cultrue/src/infrastructure/` - 基础设施层
- `/Users/gelin/Desktop/store/dev/python/ai/cultrue/src/interfaces/` - 接口层

## 验证计划

### 单元测试
- 使用pytest + pytest-asyncio
- 测试覆盖率目标：80%+
- Mock数据库和外部服务

### 集成测试
- 使用TestClient测试API端点
- 测试数据库事务
- 测试认证流程

### 端到端测试
1. 用户注册 → 登录 → 获取token
2. 使用token访问受保护的API
3. 添加Agent到我的列表
4. 通过cultrue调用agent服务的聊天API
5. 验证web-app可以正常使用新的认证系统

### 性能测试
- 使用locust进行压力测试
- 目标：支持1000并发用户
- 响应时间：P95 < 200ms

## 风险和注意事项

1. **数据库迁移**：需要与agent项目的数据库协调，避免冲突
2. **认证安全**：确保JWT密钥安全，使用强密码策略
3. **API版本管理**：预留API版本控制机制（/api/v1/）
4. **跨域问题**：正确配置CORS，支持web-app的开发和生产环境
5. **性能优化**：使用数据库索引，实现查询缓存
6. **错误处理**：统一的错误响应格式，与agent项目保持一致
7. **日志记录**：记录关键操作，便于调试和审计

## 下一步行动

1. ✅ 确认技术栈和架构设计
2. ✅ 确认数据库设计（包括消息系统）
3. ✅ 确认消息系统设计（支持User-User、User-Agent、Agent-Agent通信）
4. ⬜ 确认迭代计划的优先级
5. ⬜ 开始第一阶段：基础架构搭建

## 相关文档

- [消息系统设计文档](./messaging_system_design.md) - 详细的消息系统架构和实现方案
