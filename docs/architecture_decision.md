# 架构决策：使用Participant中间表保证数据完整性

## 决策背景

在设计支持User-User、User-Agent、Agent-Agent多类型通信的系统时，面临数据完整性保证的选择：

- **方案A**：应用层校验（无外键约束）
- **方案B**：数据库层保证（使用中间表）

## 最终决策

**采用方案B3：使用Participant中间表**

## 核心设计

### 1. 双层抽象

**领域层**：Actor值对象（轻量级抽象）
```python
@dataclass(frozen=True)
class Actor:
    """Actor值对象，用于领域层的统一抽象。"""
    actor_type: ActorType  # USER or AGENT
    actor_id: UUID         # user_id or agent_id
```

**数据库层**：Participant实体（数据完整性保证）
```sql
CREATE TABLE participants (
    id UUID PRIMARY KEY,
    participant_type VARCHAR(20) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    CONSTRAINT check_participant_type CHECK (
        (participant_type = 'user' AND user_id IS NOT NULL AND agent_id IS NULL) OR
        (participant_type = 'agent' AND agent_id IS NOT NULL AND user_id IS NULL)
    ),
    CONSTRAINT unique_user_participant UNIQUE (user_id),
    CONSTRAINT unique_agent_participant UNIQUE (agent_id)
);
```

### 2. 关系映射

```
领域层 Actor ←→ 数据库层 Participant

Actor.from_user(user_id) → Participant(participant_type='user', user_id=user_id)
Actor.from_agent(agent_id) → Participant(participant_type='agent', agent_id=agent_id)
```

### 3. 使用Participant的表

```sql
-- contacts表
CREATE TABLE contacts (
    owner_id UUID REFERENCES participants(id) ON DELETE CASCADE,
    target_id UUID REFERENCES participants(id) ON DELETE CASCADE
);

-- conversation_members表
CREATE TABLE conversation_members (
    participant_id UUID REFERENCES participants(id) ON DELETE CASCADE
);

-- messages表
CREATE TABLE messages (
    sender_id UUID REFERENCES participants(id) ON DELETE CASCADE
);
```

## 设计优势

### 1. 数据完整性（数据库层保证）

✅ **外键约束**：
- 无法插入不存在的user_id或agent_id
- User/Agent删除时自动级联删除相关记录
- 数据库层面保证一致性

✅ **唯一性约束**：
- 每个User只有一个Participant记录
- 每个Agent只有一个Participant记录
- 防止重复创建

✅ **CHECK约束**：
- 确保participant_type与user_id/agent_id匹配
- 防止数据错误

### 2. 领域模型清晰（应用层抽象）

✅ **Actor值对象**：
- 领域层使用轻量级Actor
- 业务逻辑不关心Participant
- 代码简洁易读

✅ **自动转换**：
- 仓储层负责Actor ↔ Participant转换
- 应用层无感知
- 关注点分离

### 3. 性能优化

✅ **减少验证查询**：
- 无需应用层验证Actor有效性
- 数据库外键自动验证
- 减少数据库往返

✅ **查询优化**：
- 可以直接JOIN participants表
- 利用外键索引
- 查询性能更好

## 实现策略

### 1. Participant自动管理

**原则**：Participant对应用层透明，由仓储层自动管理

```python
# 应用层代码（使用Actor）
actor = Actor.from_user(user_id)
contact = Contact.create(owner=actor, target=target_actor)
await contact_repo.save(contact)

# 仓储层实现（自动处理Participant）
class PostgresContactRepository:
    async def save(self, contact: Contact) -> Contact:
        # 1. 确保owner的Participant存在
        owner_participant = await self._ensure_participant(contact.owner)

        # 2. 确保target的Participant存在
        target_participant = await self._ensure_participant(contact.target)

        # 3. 保存contact（使用participant_id）
        contact_model = ContactModel(
            owner_id=owner_participant.id,
            target_id=target_participant.id,
            ...
        )
        await self.session.add(contact_model)

    async def _ensure_participant(self, actor: Actor) -> Participant:
        """确保Participant存在，不存在则创建。"""
        if actor.is_user():
            participant = await self.session.execute(
                select(ParticipantModel).where(
                    ParticipantModel.user_id == actor.actor_id
                )
            )
            if not participant:
                participant = ParticipantModel(
                    participant_type='user',
                    user_id=actor.actor_id
                )
                await self.session.add(participant)
        else:
            # Agent同理
            ...
        return participant
```

### 2. 查询时转换回Actor

```python
class PostgresContactRepository:
    async def find_by_owner(self, owner: Actor) -> List[Contact]:
        # 1. 查找owner的participant
        owner_participant = await self._find_participant(actor)

        # 2. 查询contacts
        results = await self.session.execute(
            select(ContactModel)
            .where(ContactModel.owner_id == owner_participant.id)
            .join(ContactModel.target_participant)
        )

        # 3. 转换为领域实体（使用Actor）
        contacts = []
        for model in results:
            contact = Contact(
                owner=self._participant_to_actor(model.owner_participant),
                target=self._participant_to_actor(model.target_participant),
                ...
            )
            contacts.append(contact)
        return contacts

    def _participant_to_actor(self, participant: ParticipantModel) -> Actor:
        """将Participant转换为Actor。"""
        if participant.participant_type == 'user':
            return Actor.from_user(participant.user_id)
        else:
            return Actor.from_agent(participant.agent_id)
```

## 与原设计的差异

### 迭代6变化

**原设计**：
- contacts表直接使用(owner_type, owner_id)
- 无外键约束
- 应用层验证

**新设计**：
- contacts表使用participant_id外键
- Participant中间表
- 数据库层验证

### 迭代7变化

**原设计**：
- conversation_members使用(actor_type, actor_id)
- messages使用(sender_type, sender_id)
- 无外键约束

**新设计**：
- conversation_members使用participant_id外键
- messages使用sender_id外键（指向participants）
- 数据库层验证

### 迭代8变化

**原设计**：
- ActorValidationService验证Actor有效性
- API接受ActorSchema

**新设计**：
- 移除ActorValidationService（不再需要）
- API仍接受ActorSchema
- 仓储层自动处理Participant

## 迁移路径

### 阶段1：添加Participant表
```sql
CREATE TABLE participants (...);
```

### 阶段2：更新现有表
```sql
-- 为contacts添加participant_id外键
ALTER TABLE contacts ADD COLUMN owner_participant_id UUID;
ALTER TABLE contacts ADD COLUMN target_participant_id UUID;

-- 迁移数据
-- 为每个(owner_type, owner_id)创建Participant
-- 更新contacts的participant_id

-- 删除旧字段
ALTER TABLE contacts DROP COLUMN owner_type;
ALTER TABLE contacts DROP COLUMN owner_id;
ALTER TABLE contacts DROP COLUMN target_type;
ALTER TABLE contacts DROP COLUMN target_id;

-- 重命名新字段
ALTER TABLE contacts RENAME COLUMN owner_participant_id TO owner_id;
ALTER TABLE contacts RENAME COLUMN target_participant_id TO target_id;

-- 添加外键约束
ALTER TABLE contacts ADD FOREIGN KEY (owner_id) REFERENCES participants(id);
ALTER TABLE contacts ADD FOREIGN KEY (target_id) REFERENCES participants(id);
```

### 阶段3：更新应用代码
- 仓储层实现_ensure_participant方法
- 仓储层实现Actor ↔ Participant转换
- 应用层代码无需修改（仍使用Actor）

## 总结

**方案B3的核心价值**：
1. **数据完整性**：数据库外键保证，无孤儿记录
2. **领域清晰**：应用层仍使用Actor抽象
3. **性能优化**：减少验证查询，利用外键索引
4. **关注点分离**：Participant对应用层透明

**权衡**：
- 增加一张中间表（participants）
- 仓储层需要处理Actor ↔ Participant转换
- 但换来了数据完整性和性能优化

**结论**：这是一个工程上的最佳实践，值得采用。

---

**决策日期**: 2026-03-16
**决策人**: 架构团队
**影响范围**: 迭代6、7、8
