# 迭代11: Agent触发器

> 实现Agent主动消息机制和触发器系统

## 📋 迭代信息

- **迭代编号**: 11
- **预计时间**: 2天
- **当前状态**: ⬜ 未开始
- **依赖迭代**: 迭代10 ✅
- **开始日期**: 待定

## 🎯 迭代目标

实现Agent主动发起消息的机制，包括触发器系统、定时任务和事件驱动的Agent消息。Agent可以主动向用户发送消息，而不仅仅是被动响应。

## 💡 设计理念

**Agent作为一等公民**：
- Agent可以主动发起会话
- Agent可以主动发送消息
- Agent可以响应系统事件
- 与User在消息系统中完全平等

**触发器类型**：
- 定时触发（Scheduled）：按时间计划发送
- 事件触发（Event-driven）：响应系统事件
- 条件触发（Conditional）：满足条件时发送
- 手动触发（Manual）：通过API手动触发

## 📝 任务清单

### 1. Agent触发器领域模型

**任务**:
- [ ] 创建TriggerType枚举
- [ ] 创建TriggerStatus枚举
- [ ] 创建AgentTrigger实体
- [ ] 创建AgentTriggerRepository接口

**交付物**:
- `src/domain/agent/enums/trigger_type.py`
- `src/domain/agent/enums/trigger_status.py`
- `src/domain/agent/entities/agent_trigger.py`
- `src/domain/agent/repositories/agent_trigger_repository.py`

**设计要点**:
```python
class TriggerType(str, Enum):
    SCHEDULED = "scheduled"    # 定时触发
    EVENT = "event"            # 事件触发
    CONDITIONAL = "conditional" # 条件触发
    MANUAL = "manual"          # 手动触发

class TriggerStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AgentTrigger:
    """Agent触发器实体。"""
    id: UUID
    agent_id: UUID
    trigger_type: TriggerType
    status: TriggerStatus
    name: str
    description: Optional[str]
    config: dict  # 触发器配置（cron表达式、事件类型等）
    target_conversation_id: Optional[UUID]  # 目标会话
    target_actor: Optional[Actor]  # 目标Actor（用于创建新会话）
    message_template: str  # 消息模板
    metadata: Optional[dict]
    last_triggered_at: Optional[datetime]
    next_trigger_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    def is_active(self) -> bool:
        return self.status == TriggerStatus.ACTIVE

    def should_trigger_now(self) -> bool:
        """检查是否应该立即触发。"""
        if not self.is_active():
            return False
        if self.next_trigger_at is None:
            return False
        return datetime.now(timezone.utc) >= self.next_trigger_at

    @classmethod
    def create_scheduled(
        cls,
        agent_id: UUID,
        name: str,
        cron_expression: str,
        message_template: str,
        target_conversation_id: UUID = None,
        target_actor: Actor = None
    ) -> "AgentTrigger":
        """创建定时触发器。"""
        return cls(
            id=uuid4(),
            agent_id=agent_id,
            trigger_type=TriggerType.SCHEDULED,
            status=TriggerStatus.ACTIVE,
            name=name,
            description=None,
            config={"cron": cron_expression},
            target_conversation_id=target_conversation_id,
            target_actor=target_actor,
            message_template=message_template,
            metadata=None,
            last_triggered_at=None,
            next_trigger_at=calculate_next_trigger(cron_expression),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
```

### 2. Agent触发器数据库模型

**任务**:
- [ ] 创建AgentTriggerModel
- [ ] 创建数据库迁移脚本
- [ ] 创建PostgresAgentTriggerRepository

**交付物**:
- `src/infrastructure/persistence/models/agent_trigger_model.py`
- `migrations/versions/xxx_create_agent_triggers_table.py`
- `src/infrastructure/persistence/repositories/postgres_agent_trigger_repository.py`

**数据库表设计**:
```sql
CREATE TABLE agent_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    trigger_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    name VARCHAR(200) NOT NULL,
    description TEXT,
    config JSONB NOT NULL DEFAULT '{}',
    target_conversation_id UUID REFERENCES conversations(id),
    target_actor_type VARCHAR(20),
    target_actor_id UUID,
    message_template TEXT NOT NULL,
    metadata JSONB,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    next_trigger_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_triggers_agent_id ON agent_triggers(agent_id);
CREATE INDEX idx_agent_triggers_status ON agent_triggers(status);
CREATE INDEX idx_agent_triggers_next_trigger_at ON agent_triggers(next_trigger_at);
```

### 3. Agent触发器应用层

**任务**:
- [ ] 创建CreateTriggerCommand和Handler
- [ ] 创建UpdateTriggerCommand和Handler
- [ ] 创建DeleteTriggerCommand和Handler
- [ ] 创建ExecuteTriggerCommand和Handler
- [ ] 创建ListTriggersQuery和Handler
- [ ] 创建TriggerDTO

**交付物**:
- `src/application/agent/commands/create_trigger_command.py`
- `src/application/agent/commands/update_trigger_command.py`
- `src/application/agent/commands/delete_trigger_command.py`
- `src/application/agent/commands/execute_trigger_command.py`
- `src/application/agent/queries/list_triggers_query.py`
- `src/application/agent/dtos/trigger_dto.py`

**ExecuteTriggerCommand设计**:
```python
@dataclass
class ExecuteTriggerCommand:
    """执行触发器命令。"""
    trigger_id: UUID
    agent_actor: Actor  # 执行的Agent

class ExecuteTriggerCommandHandler:
    def __init__(
        self,
        trigger_repo: AgentTriggerRepository,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        event_bus: EventBus
    ):
        ...

    async def handle(self, command: ExecuteTriggerCommand) -> MessageDTO:
        """执行触发器，发送消息。"""
        # 1. 获取触发器
        trigger = await self.trigger_repo.find_by_id(command.trigger_id)
        if not trigger or not trigger.is_active():
            raise NotFoundException("Trigger not found or inactive")

        # 2. 确定目标会话
        conversation_id = trigger.target_conversation_id
        if not conversation_id and trigger.target_actor:
            # 查找或创建与目标Actor的会话
            existing = await self.conversation_repo.find_direct_conversation(
                command.agent_actor, trigger.target_actor
            )
            if existing:
                conversation_id = existing.id
            else:
                # 创建新会话
                conversation = Conversation.create_direct(
                    command.agent_actor, trigger.target_actor
                )
                saved = await self.conversation_repo.save(conversation)
                conversation_id = saved.id

        if not conversation_id:
            raise ValueError("No target conversation or actor specified")

        # 3. 渲染消息模板
        content = self._render_template(trigger.message_template, {
            "agent_id": str(command.agent_actor.actor_id),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # 4. 发送消息
        message = Message.create(
            conversation_id=conversation_id,
            sender=command.agent_actor,
            content=content,
            message_type=MessageType.TEXT
        )
        saved_message = await self.message_repo.save(message)

        # 5. 发布事件（触发WebSocket推送）
        event = MessageEvent.from_message(saved_message, "message_sent")
        await self.event_bus.publish(event)

        # 6. 更新触发器状态
        trigger.last_triggered_at = datetime.now(timezone.utc)
        if trigger.trigger_type == TriggerType.SCHEDULED:
            trigger.next_trigger_at = calculate_next_trigger(
                trigger.config["cron"]
            )
        await self.trigger_repo.update(trigger)

        return MessageDTO.from_entity(saved_message)

    def _render_template(self, template: str, context: dict) -> str:
        """渲染消息模板。"""
        for key, value in context.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template
```

### 4. 定时触发器调度器

**任务**:
- [ ] 创建TriggerScheduler服务
- [ ] 实现cron表达式解析
- [ ] 实现定时任务执行
- [ ] 实现触发器状态管理

**交付物**:
- `src/application/agent/services/trigger_scheduler.py`

**设计要点**:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

class TriggerScheduler:
    """触发器调度器。"""

    def __init__(
        self,
        trigger_repo: AgentTriggerRepository,
        execute_handler: ExecuteTriggerCommandHandler,
        check_interval_seconds: int = 60
    ):
        self.trigger_repo = trigger_repo
        self.execute_handler = execute_handler
        self.check_interval_seconds = check_interval_seconds
        self.scheduler = AsyncIOScheduler()

    async def check_and_execute_triggers(self) -> None:
        """检查并执行到期的触发器。"""
        try:
            # 查询所有到期的活跃触发器
            due_triggers = await self.trigger_repo.find_due_triggers()

            for trigger in due_triggers:
                try:
                    agent_actor = Actor.from_agent(trigger.agent_id)
                    command = ExecuteTriggerCommand(
                        trigger_id=trigger.id,
                        agent_actor=agent_actor
                    )
                    await self.execute_handler.handle(command)
                    logger.info(f"Trigger {trigger.id} executed successfully")
                except Exception as e:
                    logger.error(f"Failed to execute trigger {trigger.id}: {e}")
                    # 更新触发器状态为失败
                    trigger.status = TriggerStatus.FAILED
                    await self.trigger_repo.update(trigger)

        except Exception as e:
            logger.error(f"Trigger scheduler error: {e}")

    def start(self) -> None:
        """启动调度器。"""
        self.scheduler.add_job(
            self.check_and_execute_triggers,
            'interval',
            seconds=self.check_interval_seconds
        )
        self.scheduler.start()
        logger.info(f"Trigger scheduler started (interval={self.check_interval_seconds}s)")

    def stop(self) -> None:
        """停止调度器。"""
        self.scheduler.shutdown()
        logger.info("Trigger scheduler stopped")
```

### 5. Agent触发器REST API

**任务**:
- [ ] 创建TriggerSchema（Pydantic模型）
- [ ] 实现POST /api/agents/{agent_id}/triggers - 创建触发器
- [ ] 实现GET /api/agents/{agent_id}/triggers - 获取触发器列表
- [ ] 实现GET /api/agents/{agent_id}/triggers/{trigger_id} - 获取触发器详情
- [ ] 实现PUT /api/agents/{agent_id}/triggers/{trigger_id} - 更新触发器
- [ ] 实现DELETE /api/agents/{agent_id}/triggers/{trigger_id} - 删除触发器
- [ ] 实现POST /api/agents/{agent_id}/triggers/{trigger_id}/execute - 手动执行

**交付物**:
- `src/interfaces/api/schemas/trigger_schema.py`
- `src/interfaces/api/rest/trigger.py`

**API设计**:
```python
# CreateTriggerRequest
class CreateTriggerRequest(BaseModel):
    trigger_type: str  # "scheduled", "manual"
    name: str
    description: Optional[str] = None
    config: dict  # {"cron": "0 9 * * *"} for scheduled
    target_conversation_id: Optional[str] = None
    target_actor: Optional[ActorSchema] = None
    message_template: str

# POST /api/agents/{agent_id}/triggers
# 请求: {
#   "trigger_type": "scheduled",
#   "name": "Daily Greeting",
#   "config": {"cron": "0 9 * * *"},
#   "target_actor": {"actor_type": "user", "actor_id": "uuid"},
#   "message_template": "Good morning! Today is {timestamp}"
# }
# 响应: {
#   "code": 201,
#   "data": {
#     "id": "uuid",
#     "trigger_type": "scheduled",
#     "name": "Daily Greeting",
#     "status": "active",
#     "next_trigger_at": "2026-03-18T09:00:00Z"
#   }
# }

# POST /api/agents/{agent_id}/triggers/{trigger_id}/execute
# 手动触发（无请求体）
# 响应: {
#   "code": 200,
#   "data": {
#     "message_id": "uuid",
#     "conversation_id": "uuid",
#     "content": "Good morning! Today is 2026-03-17T..."
#   }
# }
```

### 6. 事件触发器

**任务**:
- [ ] 创建EventTriggerHandler
- [ ] 实现用户上线触发
- [ ] 实现消息接收触发
- [ ] 注册事件监听器

**交付物**:
- `src/application/agent/handlers/event_trigger_handler.py`

**设计要点**:
```python
class EventTriggerHandler:
    """事件触发器处理器。"""

    def __init__(
        self,
        trigger_repo: AgentTriggerRepository,
        execute_handler: ExecuteTriggerCommandHandler
    ):
        self.trigger_repo = trigger_repo
        self.execute_handler = execute_handler

    async def on_user_online(self, actor: Actor) -> None:
        """用户上线时触发。"""
        if not actor.is_user():
            return

        # 查找所有监听用户上线事件的触发器
        triggers = await self.trigger_repo.find_by_event(
            event_type="user_online",
            target_actor=actor
        )

        for trigger in triggers:
            try:
                agent_actor = Actor.from_agent(trigger.agent_id)
                command = ExecuteTriggerCommand(
                    trigger_id=trigger.id,
                    agent_actor=agent_actor
                )
                await self.execute_handler.handle(command)
            except Exception as e:
                logger.error(f"Event trigger failed: {e}")

    async def on_message_received(self, event: MessageEvent) -> None:
        """消息接收时触发（Agent响应）。"""
        if not event.sender.is_user():
            return

        # 查找会话中的Agent成员
        conversation = await self.conversation_repo.find_by_id(
            event.conversation_id
        )
        if not conversation:
            return

        for member in conversation.members:
            if not member.is_agent():
                continue

            # 查找该Agent的消息响应触发器
            triggers = await self.trigger_repo.find_by_event(
                event_type="message_received",
                agent_id=member.actor_id
            )

            for trigger in triggers:
                try:
                    command = ExecuteTriggerCommand(
                        trigger_id=trigger.id,
                        agent_actor=member
                    )
                    await self.execute_handler.handle(command)
                except Exception as e:
                    logger.error(f"Message response trigger failed: {e}")
```

### 7. 集成到main.py

**任务**:
- [ ] 注册触发器路由
- [ ] 启动触发器调度器
- [ ] 注册事件触发器监听器
- [ ] 配置依赖注入

**交付物**:
- 更新 `main.py`

**集成要点**:
```python
from src.interfaces.api.rest import trigger as trigger_router
from src.application.agent.services.trigger_scheduler import TriggerScheduler
from src.application.agent.handlers.event_trigger_handler import EventTriggerHandler

trigger_scheduler = None
event_trigger_handler = None

@app.on_event("startup")
async def startup_event():
    global trigger_scheduler, event_trigger_handler

    # 启动触发器调度器
    trigger_scheduler = TriggerScheduler(
        trigger_repo=get_trigger_repo(),
        execute_handler=get_execute_trigger_handler()
    )
    trigger_scheduler.start()

    # 注册事件触发器
    event_trigger_handler = EventTriggerHandler(
        trigger_repo=get_trigger_repo(),
        execute_handler=get_execute_trigger_handler()
    )

    # 订阅事件
    event_bus.subscribe("user_online", event_trigger_handler.on_user_online)
    event_bus.subscribe("message_sent", event_trigger_handler.on_message_received)

    logger.info("Agent trigger system initialized")

@app.on_event("shutdown")
async def shutdown_event():
    if trigger_scheduler:
        trigger_scheduler.stop()

# 注册路由
app.include_router(trigger_router.router, tags=["triggers"])
```

### 8. 测试

**任务**:
- [ ] 编写AgentTrigger实体单元测试
- [ ] 编写ExecuteTriggerCommand单元测试
- [ ] 编写TriggerScheduler单元测试
- [ ] 编写触发器API集成测试
- [ ] 测试定时触发
- [ ] 测试手动触发
- [ ] 测试事件触发

**交付物**:
- `tests/unit/domain/agent/test_agent_trigger.py`
- `tests/unit/application/agent/test_execute_trigger_command.py`
- `tests/unit/application/agent/test_trigger_scheduler.py`
- `tests/integration/test_trigger_api.py`

**测试场景**:
```python
# 场景1: 创建定时触发器
async def test_create_scheduled_trigger():
    """测试创建定时触发器。"""
    api_key = agent.api_key.value
    response = await client.post(
        f"/api/agents/{agent_id}/triggers",
        json={
            "trigger_type": "scheduled",
            "name": "Daily Greeting",
            "config": {"cron": "0 9 * * *"},
            "target_actor": {
                "actor_type": "user",
                "actor_id": str(user_id)
            },
            "message_template": "Good morning!"
        },
        headers={"Authorization": f"ApiKey {api_key}"}
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["trigger_type"] == "scheduled"
    assert data["status"] == "active"
    assert data["next_trigger_at"] is not None

# 场景2: 手动执行触发器
async def test_manual_trigger_execution():
    """测试手动执行触发器。"""
    api_key = agent.api_key.value

    # 创建触发器
    trigger_response = await client.post(
        f"/api/agents/{agent_id}/triggers",
        json={
            "trigger_type": "manual",
            "name": "Test Trigger",
            "config": {},
            "target_actor": {
                "actor_type": "user",
                "actor_id": str(user_id)
            },
            "message_template": "Hello from Agent!"
        },
        headers={"Authorization": f"ApiKey {api_key}"}
    )
    trigger_id = trigger_response.json()["data"]["id"]

    # 手动执行
    response = await client.post(
        f"/api/agents/{agent_id}/triggers/{trigger_id}/execute",
        headers={"Authorization": f"ApiKey {api_key}"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["content"] == "Hello from Agent!"

# 场景3: 触发器执行后消息推送
async def test_trigger_execution_with_push():
    """测试触发器执行后消息通过WebSocket推送。"""
    token = create_jwt_token(user_id)
    api_key = agent.api_key.value

    async with websocket_client(f"/ws?token={token}") as ws:
        await ws.receive_json()  # 连接成功

        # Agent手动执行触发器
        response = await client.post(
            f"/api/agents/{agent_id}/triggers/{trigger_id}/execute",
            headers={"Authorization": f"ApiKey {api_key}"}
        )
        assert response.status_code == 200

        # User应该通过WebSocket收到消息
        message = await ws.receive_json()
        assert message["type"] == "new_message"
        assert message["data"]["sender"]["actor_type"] == "agent"

# 场景4: 定时触发器自动执行
async def test_scheduled_trigger_auto_execution():
    """测试定时触发器自动执行。"""
    # 创建一个立即触发的触发器（next_trigger_at = now）
    trigger = AgentTrigger.create_scheduled(
        agent_id=agent_id,
        name="Immediate Test",
        cron_expression="* * * * *",  # 每分钟
        message_template="Scheduled message",
        target_actor=Actor.from_user(user_id)
    )
    # 设置为立即触发
    trigger.next_trigger_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await trigger_repo.save(trigger)

    # 执行调度检查
    await trigger_scheduler.check_and_execute_triggers()

    # 验证消息已发送
    messages = await message_repo.find_by_conversation_id(conversation_id)
    assert len(messages) > 0
    assert messages[-1].content == "Scheduled message"

# 场景5: 权限控制 - 只有Agent可以管理自己的触发器
async def test_trigger_permission_control():
    """测试触发器权限控制。"""
    # 其他Agent尝试访问触发器
    other_api_key = other_agent.api_key.value
    response = await client.get(
        f"/api/agents/{agent_id}/triggers",
        headers={"Authorization": f"ApiKey {other_api_key}"}
    )
    assert response.status_code == 403
```

## ✅ 验收标准

- [ ] Agent可以创建定时触发器
- [ ] Agent可以创建手动触发器
- [ ] 定时触发器按计划自动执行
- [ ] 手动触发器可以通过API触发
- [ ] 触发器执行后消息通过WebSocket推送
- [ ] 事件触发器响应系统事件
- [ ] 权限控制正确（只有Agent可以管理自己的触发器）
- [ ] 触发器状态正确更新
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 代码符合编码规范

## 🔧 技术要点

### 1. 触发器类型

| 类型 | 触发条件 | 配置示例 |
|------|----------|----------|
| scheduled | cron表达式 | `{"cron": "0 9 * * *"}` |
| event | 系统事件 | `{"event": "user_online"}` |
| conditional | 条件满足 | `{"condition": "unread_count > 5"}` |
| manual | 手动触发 | `{}` |

### 2. 消息模板

支持变量替换：
```
"Good morning {user_name}! Today is {date}."
```

可用变量：
- `{agent_id}` - Agent ID
- `{timestamp}` - 当前时间
- `{date}` - 当前日期
- `{conversation_id}` - 会话ID

### 3. Cron表达式

使用标准5字段cron格式：
```
分 时 日 月 周
0 9 * * *    # 每天9点
0 */2 * * *  # 每2小时
*/30 * * * * # 每30分钟
```

### 4. 触发器执行流程

```
触发条件满足
    ↓
ExecuteTriggerCommand
    ↓
确定目标会话（已有或新建）
    ↓
渲染消息模板
    ↓
创建并保存Message
    ↓
发布MessageEvent
    ↓
WebSocket推送给在线用户
    ↓
更新触发器状态
```

### 5. 错误处理

触发器执行失败时：
- 记录错误日志
- 更新触发器状态为FAILED
- 不影响其他触发器执行
- 可以配置重试策略

### 6. 扩展性

当前实现为单机版，后续可以扩展：
- 分布式调度（使用Redis锁防止重复执行）
- 触发器执行历史记录
- 触发器执行统计
- 更复杂的条件触发逻辑

## 🔜 下一步

完成迭代11后，里程碑3达成！进入**里程碑4: 完整功能**，从**迭代12: 地图功能**开始。

## 📊 预期成果

完成本迭代后，系统将具备：
- ✅ Agent主动消息机制
- ✅ 定时触发器（cron）
- ✅ 手动触发器
- ✅ 事件触发器
- ✅ 消息模板系统
- ✅ 触发器管理API
- ✅ 完整的测试覆盖
- ✅ 里程碑3完成（实时通信系统）

---

**创建日期**: 2026-03-17
**文档版本**: v1.0
