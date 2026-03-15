# 设计更新总结

## 更新日期
2026-03-15

## 更新原因
用户提出了新的需求：系统需要支持多方通信，包括：
1. 人类和人类之间可以聊天
2. 人类和agent智能体可以聊天
3. agent和agent智能体之间可以聊天
4. agent会主动给人类发送消息
5. agent可以主动给其他agent发送消息

原有设计只考虑了"用户与Agent聊天"的场景，不满足新需求。

## 主要更新内容

### 1. 新增消息系统设计文档
创建了 `messaging_system_design.md`，包含：

#### 数据库设计（5张新表）
- **conversations表**：会话表，支持direct和group类型
- **conversation_participants表**：会话参与者表，支持user和agent两种参与者类型
- **messages表**：消息表，支持多种消息类型
- **message_read_status表**：消息已读状态表
- **agent_triggers表**：Agent触发器配置表

#### DDD架构设计
- 新增 `messaging` 领域
- 包含完整的实体、值对象、仓储接口和领域服务

#### API设计
- **REST API**：会话管理、消息管理、未读消息、触发器管理
- **WebSocket API**：实时消息推送、输入状态、消息已读等

#### Agent主动消息机制
支持4种触发器类型：
1. 定时触发（Scheduled Trigger）
2. 事件触发（Event-Based Trigger）
3. 关键词触发（Keyword Trigger）
4. 上下文变化触发（Context Change Trigger）

#### 技术栈更新
新增依赖：
- websockets 12.0+ - WebSocket支持
- redis 5.0+ - 连接管理和消息队列
- celery 5.3+ - 异步任务队列
- apscheduler 3.10+ - 定时任务调度
- aioredis 2.0+ - 异步Redis客户端

#### 实现计划
分为4个阶段：
- Phase 1: 基础消息系统（3-4天）
- Phase 2: WebSocket实时通信（2-3天）
- Phase 3: Agent主动消息（2-3天）
- Phase 4: 优化和完善（1-2天）

### 2. 更新主开发计划文档
更新了 `backend_development_plan.md`：

#### 新增核心通信需求部分
明确列出了4种通信场景的支持

#### 更新DDD架构设计
- 添加了 `messaging` 领域
- 添加了相关的应用层、基础设施层和接口层组件
- 标注了新增的文件和模块（⭐标记）

#### 更新数据库设计
添加了对消息系统表的引用

#### 更新技术栈和依赖
添加了WebSocket、Redis、Celery等新依赖

#### 更新迭代计划
新增了4个消息系统相关的开发阶段（第七至第十阶段）：
- 第七阶段：消息系统 - 基础功能（3-4天）
- 第八阶段：消息系统 - WebSocket实时通信（2-3天）
- 第九阶段：消息系统 - Agent主动消息（2-3天）
- 第十阶段：消息系统 - 优化和完善（1-2天）

#### 更新下一步行动
添加了对消息系统设计的确认项

## 核心设计亮点

### 1. 参与者抽象
User和Agent都被抽象为"参与者"（Participant），使用统一的接口：
- participant_type: 'user' 或 'agent'
- participant_id: 指向users.id或agents.id

这种设计使得系统可以灵活支持任意类型参与者之间的通信。

### 2. 会话中心设计
所有消息都属于某个会话（Conversation），会话可以是：
- direct（单聊）：两个参与者
- group（群聊）：多个参与者

### 3. 实时推送机制
使用WebSocket实现实时消息推送，支持：
- 新消息推送
- 消息已读状态
- 输入状态指示
- Agent主动发起的消息

### 4. Agent主动消息机制
通过触发器系统实现Agent的主动行为：
- 定时触发：按时间表发送消息
- 事件触发：响应系统事件
- 关键词触发：检测到特定关键词时响应
- 上下文触发：根据上下文变化主动发起

### 5. 可扩展性
- 支持多实例部署（通过Redis Pub/Sub）
- 支持水平扩展
- 支持消息缓存和性能优化

## 与现有系统的兼容性

### 与Agent项目的集成
采用混合模式：
1. 保留原有的代理转发机制（用于流式响应）
2. 新增消息系统（用于持久化存储和多方通信）
3. 两者协同工作，互不冲突

### 数据迁移
如果agent项目已有conversations数据，可以通过迁移脚本将数据迁移到新的消息系统。

## 安全和性能考虑

### 安全
- WebSocket连接需要JWT认证
- 权限控制：只能访问自己参与的会话
- 消息验证：长度限制、频率限制、敏感词过滤
- Agent触发器权限：只有管理员可以管理

### 性能
- 消息分页（游标分页）
- Redis缓存（会话列表、未读计数、在线状态）
- 数据库索引优化
- WebSocket连接池管理

## 文档结构

```
docs/
├── backend_development_plan.md      # 主开发计划（已更新）
├── messaging_system_design.md       # 消息系统设计（新增）
└── design_update_summary.md         # 本文档
```

## 总结

通过这次更新，系统设计已经完全支持用户提出的多方通信需求：
- ✅ User ↔ User 通信
- ✅ User ↔ Agent 通信
- ✅ Agent ↔ Agent 通信
- ✅ Agent主动发起消息

设计采用了灵活的参与者抽象和会话中心模式，不仅满足当前需求，还为未来的扩展（如群聊、多Agent协作等）预留了空间。

实现计划清晰，分为10个阶段，总计约15-20天的开发时间。

## 下一步
等待用户确认设计方案，然后开始实施第一阶段：基础架构搭建。