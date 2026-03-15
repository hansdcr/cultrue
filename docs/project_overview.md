# 项目概览

> Cultrue - 多方通信平台后端服务

## 🎯 项目简介

Cultrue是一个支持多方实时通信的后端平台，支持以下通信场景：

- **User ↔ User**: 人类之间的聊天
- **User ↔ Agent**: 人类与AI智能体的聊天
- **Agent ↔ Agent**: AI智能体之间的聊天
- **Agent主动发起**: Agent可以主动给User或其他Agent发送消息

## 🏗️ 技术架构

### 架构模式

采用**DDD（领域驱动设计）四层架构**：

```
┌─────────────────────────────────────┐
│      Interfaces Layer (接口层)       │
│   REST API / WebSocket / Schemas    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│    Application Layer (应用层)        │
│   Commands / Queries / DTOs         │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      Domain Layer (领域层)           │
│  Entities / Value Objects / Services│
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Infrastructure Layer (基础设施层)   │
│  Database / Security / External APIs│
└─────────────────────────────────────┘
```

### 技术栈

- **Web框架**: FastAPI 0.115+
- **数据库**: PostgreSQL 15+ (异步asyncpg)
- **ORM**: SQLAlchemy 2.0 + Alembic
- **认证**: JWT (PyJWT) + bcrypt
- **实时通信**: WebSocket
- **消息队列**: Redis + Celery
- **任务调度**: APScheduler
- **Python版本**: 3.12

## 📦 核心领域

### 1. User（用户领域）

管理用户账户、认证和个人信息。

**核心功能**:
- 用户注册/登录
- 用户信息管理
- 用户设置

### 2. Auth（认证领域）

处理身份验证和授权。

**核心功能**:
- JWT Token生成/验证
- 密码加密/验证
- 会话管理

### 3. Agent（智能体领域）

管理AI智能体的配置和行为。

**核心功能**:
- Agent信息管理
- Agent配置
- 用户与Agent关联

### 4. Messaging（消息领域）

处理多方通信和消息管理。

**核心功能**:
- 会话管理
- 消息发送/接收
- 实时推送
- Agent主动消息

### 5. Map（地图领域）

管理地理位置和文化地图。

**核心功能**:
- 位置管理
- 位置搜索
- 附近位置查询

## 🗄️ 数据模型

### 核心表

1. **users** - 用户表
2. **agents** - Agent表
3. **sessions** - 会话表（认证）
4. **conversations** - 会话表（消息）
5. **conversation_participants** - 会话参与者
6. **messages** - 消息表
7. **message_read_status** - 消息已读状态
8. **agent_triggers** - Agent触发器
9. **locations** - 位置表
10. **user_settings** - 用户设置

详细设计见：[数据库设计文档](./backend_development_plan.md#数据库设计)

## 🔌 API设计

### REST API

- **认证**: `/api/auth/*`
- **用户**: `/api/users/*`
- **Agent**: `/api/agents/*`
- **消息**: `/api/conversations/*`, `/api/messages/*`
- **地图**: `/api/locations/*`
- **设置**: `/api/settings/*`

### WebSocket API

- **连接**: `WS /api/ws/chat?token={jwt_token}`
- **事件**: send_message, mark_read, typing等

详细设计见：[API设计文档](./messaging_system_design.md#api设计)

## 🔄 开发流程

### 迭代开发

项目采用迭代开发模式，分为15个迭代：

1. **迭代1-5**: 用户认证系统（里程碑1）
2. **迭代6-8**: Agent和消息系统（里程碑2）
3. **迭代9-11**: 实时通信（里程碑3）
4. **迭代12-15**: 完整功能（里程碑4）

详细计划见：[迭代计划](./iterations/README.md)

### 开发原则

1. **单一功能**: 每次只完成一个功能点
2. **测试驱动**: 每个功能都有测试
3. **文档同步**: 代码和文档同步更新
4. **代码审查**: 遵循编码规范

详细规范见：[编码规范](./coding_standards.md)

## 🎯 项目目标

### 短期目标（1-2周）

- ✅ 完成基础架构搭建
- ⬜ 完成用户认证系统
- ⬜ 完成Agent管理
- ⬜ 完成基础消息系统

### 中期目标（3-4周）

- ⬜ 完成WebSocket实时通信
- ⬜ 完成Agent主动消息
- ⬜ 完成地图功能
- ⬜ 与Agent项目集成

### 长期目标（1-2个月）

- ⬜ 性能优化
- ⬜ 完善文档
- ⬜ 生产环境部署
- ⬜ 监控和日志系统

## 🔗 相关项目

### Agent项目

AI智能体服务，提供聊天、会话管理、记忆系统。

- **技术栈**: FastAPI + PostgreSQL + DDD
- **集成方式**: HTTP API调用
- **数据同步**: 共享用户和Agent信息

### Web-App项目

前端应用，React + Vite实现。

- **技术栈**: React + Vite + TypeScript
- **集成方式**: REST API + WebSocket
- **页面**: 首页、聊天、发现、联系人、设置

## 📊 项目状态

- **当前版本**: v0.1.0
- **开发状态**: 开发中
- **当前迭代**: 迭代1（85%完成）
- **总体进度**: 5%

## 👥 团队

- **后端开发**: [待添加]
- **前端开发**: [待添加]
- **AI开发**: [待添加]
- **产品经理**: [待添加]

## 📚 学习资源

- [DDD领域驱动设计](https://domain-driven-design.org/)
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [WebSocket协议](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)

---

**创建日期**: 2026-03-15
**最后更新**: 2026-03-15
**文档版本**: v1.0
