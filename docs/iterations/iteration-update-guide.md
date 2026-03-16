# 迭代6、7、8更新说明 - 采用Participant中间表方案

## 更新原因

采用**方案B3：Participant中间表**，在保持Actor值对象抽象的同时，通过数据库外键约束保证数据完整性。

## 核心变化

### 1. 架构分层

```
┌─────────────────────────────────────┐
│      应用层 & 领域层                 │
│   使用 Actor 值对象（轻量级抽象）     │
│   Actor.from_user(user_id)          │
│   Actor.from_agent(agent_id)        │
└─────────────────────────────────────┘
              ↕ (仓储层转换)
┌─────────────────────────────────────┐
│         数据库层                     │
│   使用 Participant 实体（外键保证）  │
│   participants 表                   │
│   contacts, messages 等引用          │
└─────────────────────────────────────┘
```

### 2. 关键设计原则

1. **应用层透明**：应用层代码仍使用Actor，不感知Participant
2. **仓储层转换**：仓储层负责Actor ↔ Participant的转换
3. **自动管理**：Participant由仓储层自动创建和管理
4. **数据完整性**：数据库外键约束保证一致性

## 迭代6更新要点

### 数据库表变化

**原设计**：
```sql
CREATE TABLE contacts (
    owner_type VARCHAR(20) NOT NULL,
    owner_id UUID NOT NULL,
    target_type VARCHAR(20) NOT NULL,
    target_id UUID NOT NULL
);
```

**新设计**：
```sql
-- 新增participants表
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

-- contacts表使用外键
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    contact_type VARCHAR(20) DEFAULT 'friend',
    alias VARCHAR(100),
    is_favorite BOOLEAN DEFAULT FALSE,
    last_interaction_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(owner_id, target_id)
);
```

### 领域层变化

**保持不变**：
- Actor值对象设计不变
- Contact实体仍使用Actor

**新增**：
- Participant实体（仅用于数据库映射）
- ParticipantRepository接口

### 基础设施层变化

**新增**：
- ParticipantModel（SQLAlchemy模型）
- PostgresParticipantRepository

**更新**：
- PostgresContactRepository添加_ensure_participant方法
- 实现Actor ↔ Participant转换逻辑

### 应用层变化

**移除**：
- ~~ActorValidationService~~（不再需要）

**保持不变**：
- 所有Command和Query仍使用Actor
- 业务逻辑无需修改

## 迭代7更新要点

### 数据库表变化

**原设计**：
```sql
CREATE TABLE conversation_members (
    conversation_id UUID,
    actor_type VARCHAR(20) NOT NULL,
    actor_id UUID NOT NULL
);

CREATE TABLE messages (
    sender_type VARCHAR(20) NOT NULL,
    sender_id UUID NOT NULL
);
```

**新设计**：
```sql
CREATE TABLE conversation_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    participant_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_read_at TIMESTAMP WITH TIME ZONE,
    is_muted BOOLEAN DEFAULT FALSE,
    UNIQUE(conversation_id, participant_id)
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    message_type VARCHAR(20) DEFAULT 'text',
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 领域层变化

**保持不变**：
- Conversation实体仍使用List[Actor]
- Message实体仍使用Actor作为sender

### 基础设施层变化

**更新**：
- ConversationRepository实现_ensure_participant
- MessageRepository实现_ensure_participant
- 保存时自动转换Actor → Participant
- 查询时自动转换Participant → Actor

## 迭代8更新要点

### API层变化

**保持不变**：
- API仍接受ActorSchema
- 请求/响应格式不变

**移除**：
- ~~ActorValidationService~~相关代码

**简化**：
- 不再需要手动验证Actor有效性
- 数据库外键自动保证

### 应用层变化

**Command/Query**：
- 保持使用Actor
- 移除validate_actors调用

**示例**：
```python
# 原设计
async def handle(self, command: CreateConversationCommand):
    # 验证所有成员
    await self.actor_validation_service.validate_actors(command.members)  # 移除这行

    conversation = Conversation.create_direct(...)
    return await self.repo.save(conversation)

# 新设计
async def handle(self, command: CreateConversationCommand):
    # 无需验证，仓储层会自动处理
    conversation = Conversation.create_direct(...)
    return await self.repo.save(conversation)  # 内部会ensure_participant
```

## 仓储层实现模式

### 标准模式

所有使用Actor的仓储都遵循此模式：

```python
class PostgresXxxRepository:
    def __init__(self, session, participant_repo):
        self.session = session
        self.participant_repo = participant_repo

    async def _ensure_participant(self, actor: Actor) -> ParticipantModel:
        """确保Participant存在，不存在则自动创建。"""
        return await self.participant_repo.find_or_create(actor)

    async def save(self, entity):
        # 1. 确保所有Actor对应的Participant存在
        participant = await self._ensure_participant(entity.actor)

        # 2. 使用participant.id保存
        model = XxxModel(participant_id=participant.id, ...)
        self.session.add(model)
        await self.session.flush()

        return entity

    async def find_xxx(self, actor: Actor):
        # 1. 查找Participant
        participant = await self.participant_repo.find_by_actor(actor)
        if not participant:
            return None

        # 2. 使用participant.id查询
        result = await self.session.execute(
            select(XxxModel).where(XxxModel.participant_id == participant.id)
        )

        # 3. 转换回领域实体（使用Actor）
        return self._to_entity(result)

    def _to_entity(self, model):
        # 将Participant转换回Actor
        actor = self._participant_to_actor(model.participant)
        return Entity(actor=actor, ...)

    def _participant_to_actor(self, participant: ParticipantModel) -> Actor:
        if participant.participant_type == 'user':
            return Actor.from_user(participant.user_id)
        else:
            return Actor.from_agent(participant.agent_id)
```

### ParticipantRepository实现

```python
class PostgresParticipantRepository:
    async def find_or_create(self, actor: Actor) -> ParticipantModel:
        """查找或创建Participant。"""
        if actor.is_user():
            # 查找
            result = await self.session.execute(
                select(ParticipantModel).where(
                    ParticipantModel.user_id == actor.actor_id
                )
            )
            participant = result.scalar_one_or_none()

            # 不存在则创建
            if not participant:
                participant = ParticipantModel(
                    participant_type='user',
                    user_id=actor.actor_id,
                    agent_id=None
                )
                self.session.add(participant)
                await self.session.flush()
        else:
            # Agent同理
            ...

        return participant

    async def find_by_actor(self, actor: Actor) -> Optional[ParticipantModel]:
        """根据Actor查找Participant。"""
        if actor.is_user():
            result = await self.session.execute(
                select(ParticipantModel).where(
                    ParticipantModel.user_id == actor.actor_id
                )
            )
        else:
            result = await self.session.execute(
                select(ParticipantModel).where(
                    ParticipantModel.agent_id == actor.actor_id
                )
            )
        return result.scalar_one_or_none()
```

## 测试更新

### 单元测试

**保持不变**：
- 领域层测试仍使用Actor
- 无需修改

### 集成测试

**更新**：
- 需要先创建User/Agent
- Participant会自动创建
- 测试外键约束

**示例**：
```python
async def test_contact_with_invalid_actor_should_fail():
    """测试：使用不存在的Actor创建Contact应该失败。"""
    # 创建一个不存在的Actor
    invalid_actor = Actor.from_user(uuid4())
    valid_actor = Actor.from_user(user.id)

    contact = Contact.create(owner=valid_actor, target=invalid_actor)

    # 保存时应该失败（外键约束）
    with pytest.raises(ForeignKeyViolation):
        await contact_repo.save(contact)
```

## 迁移检查清单

### 迭代6
- [ ] 添加Participant领域实体
- [ ] 添加ParticipantRepository接口
- [ ] 创建participants表迁移脚本
- [ ] 更新contacts表结构（使用外键）
- [ ] 实现PostgresParticipantRepository
- [ ] 更新PostgresContactRepository（添加_ensure_participant）
- [ ] 移除ActorValidationService
- [ ] 更新测试

### 迭代7
- [ ] 更新conversation_members表结构
- [ ] 更新messages表结构
- [ ] 更新PostgresConversationRepository
- [ ] 更新PostgresMessageRepository
- [ ] 更新测试

### 迭代8
- [ ] 移除ActorValidationService相关代码
- [ ] 简化Command Handler（移除validate_actors调用）
- [ ] 更新API文档
- [ ] 更新测试

## 优势总结

1. **数据完整性**：外键约束保证，无孤儿记录
2. **代码简洁**：应用层无需手动验证
3. **性能优化**：减少验证查询
4. **关注点分离**：Participant对应用层透明
5. **易于调试**：数据库层面就能发现问题

---

**更新日期**: 2026-03-16
**更新原因**: 采用Participant中间表保证数据完整性
