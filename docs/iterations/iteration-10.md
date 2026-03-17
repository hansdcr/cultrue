# 迭代10: WebSocket-消息推送

> 实现基于WebSocket的实时消息推送功能

## 📋 迭代信息

- **迭代编号**: 10
- **预计时间**: 1-2天
- **当前状态**: ⬜ 未开始
- **依赖迭代**: 迭代9 ✅
- **开始日期**: 待定

## 🎯 迭代目标

实现完整的实时消息推送系统，当用户发送消息时，通过WebSocket实时推送给会话中的所有在线成员。支持消息送达确认、在线状态同步和消息事件通知。

## 💡 设计理念

**事件驱动架构**：
- 消息发送触发事件
- 事件系统分发到订阅者
- WebSocket推送给在线用户

**可靠性保证**：
- 消息持久化（已在迭代8完成）
- 在线用户实时推送
- 离线用户下次上线拉取
- 消息送达确认机制

**性能优化**：
- 异步推送不阻塞API
- 批量推送优化
- 连接池复用

## 📝 任务清单

### 1. 消息事件系统

**任务**:
- [ ] 创建MessageEvent领域事件
- [ ] 创建EventBus事件总线
- [ ] 实现事件发布/订阅机制
- [ ] 创建事件处理器接口

**交付物**:
- `src/domain/messaging/events/message_event.py`
- `src/application/shared/events/event_bus.py`
- `src/application/shared/events/event_handler.py`

**设计要点**:
```python
from dataclasses import dataclass
from src.domain.shared.value_objects.actor import Actor

@dataclass
class MessageEvent:
    """消息事件。"""
    event_type: str  # "message_sent", "message_deleted", etc.
    message_id: UUID
    conversation_id: UUID
    sender: Actor
    content: str
    message_type: str
    metadata: Optional[dict]
    created_at: datetime

    @classmethod
    def from_message(cls, message: Message, event_type: str = "message_sent") -> "MessageEvent":
        """从Message实体创建事件。"""
        return cls(
            event_type=event_type,
            message_id=message.id,
            conversation_id=message.conversation_id,
            sender=message.sender,
            content=message.content,
            message_type=message.message_type.value,
            metadata=message.metadata,
            created_at=message.created_at
        )

class EventBus:
    """事件总线（内存实现）。"""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """订阅事件。"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event: MessageEvent) -> None:
        """发布事件。"""
        handlers = self._handlers.get(event.event_type, [])
        # 异步执行所有处理器
        await asyncio.gather(
            *[handler(event) for handler in handlers],
            return_exceptions=True
        )
```

### 2. 消息推送服务

**任务**:
- [ ] 创建MessagePushService
- [ ] 实现推送给会话成员
- [ ] 实现推送给特定Actor
- [ ] 处理推送失败重试
- [ ] 添加推送日志

**交付物**:
- `src/application/realtime/services/message_push_service.py`

**设计要点**:
```python
from src.application.realtime.services.connection_manager import ConnectionManager
from src.domain.messaging.repositories.conversation_repository import ConversationRepository

class MessagePushService:
    """消息推送服务。"""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        conversation_repo: ConversationRepository
    ):
        self.connection_manager = connection_manager
        self.conversation_repo = conversation_repo

    async def push_message_to_conversation(
        self,
        conversation_id: UUID,
        message_event: MessageEvent,
        exclude_sender: bool = True
    ) -> Dict[str, int]:
        """
        推送消息到会话的所有在线成员。

        Args:
            conversation_id: 会话ID
            message_event: 消息事件
            exclude_sender: 是否排除发送者

        Returns:
            推送统计 {"success": 3, "failed": 0, "offline": 2}
        """
        # 1. 获取会话成员
        conversation = await self.conversation_repo.find_by_id(conversation_id)
        if not conversation:
            return {"success": 0, "failed": 0, "offline": 0}

        # 2. 构造推送消息
        push_data = {
            "type": "new_message",
            "data": {
                "message_id": str(message_event.message_id),
                "conversation_id": str(message_event.conversation_id),
                "sender": {
                    "actor_type": message_event.sender.actor_type.value,
                    "actor_id": str(message_event.sender.actor_id)
                },
                "message_type": message_event.message_type,
                "content": message_event.content,
                "metadata": message_event.metadata,
                "created_at": message_event.created_at.isoformat()
            }
        }

        # 3. 推送给所有在线成员
        stats = {"success": 0, "failed": 0, "offline": 0}

        for member in conversation.members:
            # 排除发送者（可选）
            if exclude_sender and member == message_event.sender:
                continue

            # 检查在线状态
            if not self.connection_manager.is_online(member):
                stats["offline"] += 1
                continue

            # 推送到所有设备
            connections = self.connection_manager.get_connections(member)
            for ws in connections:
                try:
                    await ws.send_json(push_data)
                    stats["success"] += 1
                except Exception as e:
                    logger.error(f"Failed to push message to {member}: {e}")
                    stats["failed"] += 1

        return stats

    async def push_to_actor(
        self,
        actor: Actor,
        message_type: str,
        data: dict
    ) -> int:
        """
        推送消息给特定Actor的所有设备。

        Returns:
            成功推送的设备数量
        """
        if not self.connection_manager.is_online(actor):
            return 0

        push_data = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        connections = self.connection_manager.get_connections(actor)
        success_count = 0

        for ws in connections:
            try:
                await ws.send_json(push_data)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to push to {actor}: {e}")

        return success_count
```

### 3. 消息事件处理器

**任务**:
- [ ] 创建MessageSentEventHandler
- [ ] 创建MessageDeletedEventHandler
- [ ] 创建ConversationUpdatedEventHandler
- [ ] 注册事件处理器到EventBus

**交付物**:
- `src/application/realtime/handlers/message_sent_handler.py`
- `src/application/realtime/handlers/message_deleted_handler.py`

**设计要点**:
```python
class MessageSentEventHandler:
    """消息发送事件处理器。"""

    def __init__(self, push_service: MessagePushService):
        self.push_service = push_service

    async def handle(self, event: MessageEvent) -> None:
        """处理消息发送事件。"""
        try:
            # 推送消息到会话成员
            stats = await self.push_service.push_message_to_conversation(
                event.conversation_id,
                event,
                exclude_sender=True  # 不推送给发送者
            )

            logger.info(
                f"Message {event.message_id} pushed: "
                f"success={stats['success']}, "
                f"failed={stats['failed']}, "
                f"offline={stats['offline']}"
            )
        except Exception as e:
            logger.error(f"Failed to handle message_sent event: {e}")

class MessageDeletedEventHandler:
    """消息删除事件处理器。"""

    def __init__(self, push_service: MessagePushService):
        self.push_service = push_service

    async def handle(self, event: MessageEvent) -> None:
        """处理消息删除事件。"""
        try:
            # 通知会话成员消息已删除
            await self.push_service.push_message_to_conversation(
                event.conversation_id,
                event,
                exclude_sender=False  # 包括发送者
            )
        except Exception as e:
            logger.error(f"Failed to handle message_deleted event: {e}")
```

### 4. 集成到SendMessageCommand

**任务**:
- [ ] 在SendMessageCommand中发布事件
- [ ] 确保消息持久化后再发布
- [ ] 处理事件发布失败

**交付物**:
- 更新 `src/application/messaging/commands/send_message_command.py`

**集成要点**:
```python
class SendMessageCommandHandler:
    def __init__(
        self,
        message_repo: MessageRepository,
        conversation_repo: ConversationRepository,
        event_bus: EventBus  # ⭐ 注入EventBus
    ):
        self.message_repo = message_repo
        self.conversation_repo = conversation_repo
        self.event_bus = event_bus

    async def handle(self, command: SendMessageCommand) -> MessageDTO:
        # 1. 验证会话和权限
        conversation = await self.conversation_repo.find_by_id(command.conversation_id)
        if not conversation:
            raise NotFoundException("Conversation not found")

        if not conversation.has_member(command.sender):
            raise ForbiddenException("Not a member of this conversation")

        # 2. 创建并保存消息
        message = Message.create(
            conversation_id=command.conversation_id,
            sender=command.sender,
            content=command.content,
            message_type=MessageType(command.message_type),
            metadata=command.metadata
        )
        saved_message = await self.message_repo.save(message)

        # 3. 发布事件（异步推送）⭐ 新增
        event = MessageEvent.from_message(saved_message, "message_sent")
        await self.event_bus.publish(event)

        # 4. 返回DTO
        return MessageDTO.from_entity(saved_message)
```

### 5. 在线状态同步

**任务**:
- [ ] 创建OnlineStatusService
- [ ] 实现在线状态查询
- [ ] 实现在线状态变更通知
- [ ] 添加在线状态缓存

**交付物**:
- `src/application/realtime/services/online_status_service.py`

**设计要点**:
```python
class OnlineStatusService:
    """在线状态服务。"""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        push_service: MessagePushService
    ):
        self.connection_manager = connection_manager
        self.push_service = push_service

    def is_online(self, actor: Actor) -> bool:
        """检查Actor是否在线。"""
        return self.connection_manager.is_online(actor)

    def get_online_members(self, actors: List[Actor]) -> List[Actor]:
        """获取在线的成员列表。"""
        return [actor for actor in actors if self.is_online(actor)]

    async def notify_status_change(
        self,
        actor: Actor,
        status: str,  # "online" or "offline"
        conversation_ids: List[UUID]
    ) -> None:
        """
        通知会话成员Actor的在线状态变更。

        Args:
            actor: 状态变更的Actor
            status: 新状态
            conversation_ids: 需要通知的会话ID列表
        """
        notification = {
            "type": "status_change",
            "data": {
                "actor_type": actor.actor_type.value,
                "actor_id": str(actor.actor_id),
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

        # 推送给相关会话的在线成员
        for conv_id in conversation_ids:
            conversation = await self.conversation_repo.find_by_id(conv_id)
            if not conversation:
                continue

            for member in conversation.members:
                if member == actor:  # 不推送给自己
                    continue

                await self.push_service.push_to_actor(
                    member,
                    "status_change",
                    notification["data"]
                )
```

### 6. 更新WebSocket端点

**任务**:
- [ ] 连接建立时通知在线状态
- [ ] 连接断开时通知离线状态
- [ ] 添加消息送达确认
- [ ] 添加typing状态推送

**交付物**:
- 更新 `src/interfaces/websocket/endpoints.py`

**更新要点**:
```python
@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None),
    api_key: str = Query(None),
    connection_manager: ConnectionManager = Depends(get_connection_manager),
    online_status_service: OnlineStatusService = Depends(get_online_status_service),
    conversation_repo: ConversationRepository = Depends(get_conversation_repo)
):
    await websocket.accept()

    try:
        # 认证
        actor = await authenticate_websocket(websocket, token, api_key)

        # 注册连接
        connection = await connection_manager.connect(websocket, actor, metadata)

        # ⭐ 通知在线状态
        conversations = await conversation_repo.find_by_actor(actor)
        conversation_ids = [conv.id for conv in conversations]
        await online_status_service.notify_status_change(
            actor, "online", conversation_ids
        )

        # 发送连接成功消息
        await websocket.send_json({
            "type": "connection_established",
            "data": {...}
        })

        # 消息循环
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "ping":
                # 心跳
                await connection_manager.update_heartbeat(websocket)
                await websocket.send_json({"type": "pong", ...})

            elif message_type == "ack":
                # ⭐ 消息送达确认
                message_id = data.get("message_id")
                logger.info(f"Message {message_id} acknowledged by {actor}")

            elif message_type == "typing":
                # ⭐ 输入状态
                conversation_id = data.get("conversation_id")
                # 推送给会话其他成员
                ...

    except WebSocketDisconnect:
        pass
    finally:
        # 清理连接
        await connection_manager.disconnect(websocket)

        # ⭐ 通知离线状态
        conversations = await conversation_repo.find_by_actor(actor)
        conversation_ids = [conv.id for conv in conversations]
        await online_status_service.notify_status_change(
            actor, "offline", conversation_ids
        )
```

### 7. 测试

**任务**:
- [ ] 编写MessagePushService单元测试
- [ ] 编写事件处理器单元测试
- [ ] 编写WebSocket推送集成测试
- [ ] 测试多设备推送
- [ ] 测试在线状态同步
- [ ] 测试消息送达确认

**交付物**:
- `tests/unit/application/realtime/test_message_push_service.py`
- `tests/unit/application/realtime/test_message_sent_handler.py`
- `tests/integration/test_websocket_message_push.py`

**测试场景**:
```python
# 场景1: 实时消息推送
async def test_realtime_message_push():
    """测试消息实时推送给在线用户。"""
    # 1. User1和User2建立WebSocket连接
    token1 = create_jwt_token(user1_id)
    token2 = create_jwt_token(user2_id)

    async with websocket_client(f"/ws?token={token1}") as ws1:
        async with websocket_client(f"/ws?token={token2}") as ws2:
            # 接收连接成功消息
            await ws1.receive_json()
            await ws2.receive_json()

            # 2. User1通过REST API发送消息
            response = await http_client.post(
                f"/api/conversations/{conversation_id}/messages",
                json={"content": "Hello!"},
                headers={"Authorization": f"Bearer {token1}"}
            )
            assert response.status_code == 201

            # 3. User2应该通过WebSocket收到消息
            message = await ws2.receive_json()
            assert message["type"] == "new_message"
            assert message["data"]["content"] == "Hello!"
            assert message["data"]["sender"]["actor_id"] == str(user1_id)

            # 4. User1不应该收到（exclude_sender=True）
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(ws1.receive_json(), timeout=1.0)

# 场景2: 离线用户不推送
async def test_offline_user_no_push():
    """测试离线用户不会收到实时推送。"""
    # User1在线，User2离线
    token1 = create_jwt_token(user1_id)

    async with websocket_client(f"/ws?token={token1}") as ws1:
        await ws1.receive_json()

        # User2发送消息（通过REST API，未建立WebSocket）
        token2 = create_jwt_token(user2_id)
        response = await http_client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"content": "Hello!"},
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert response.status_code == 201

        # User1应该收到推送
        message = await ws1.receive_json()
        assert message["type"] == "new_message"

# 场景3: 多设备推送
async def test_multi_device_push():
    """测试同一用户多设备都收到推送。"""
    token = create_jwt_token(user_id)

    async with websocket_client(f"/ws?token={token}") as ws1:
        async with websocket_client(f"/ws?token={token}") as ws2:
            await ws1.receive_json()
            await ws2.receive_json()

            # 另一个用户发送消息
            response = await http_client.post(
                f"/api/conversations/{conversation_id}/messages",
                json={"content": "Hello!"},
                headers={"Authorization": f"Bearer {other_token}"}
            )

            # 两个设备都应该收到
            msg1 = await ws1.receive_json()
            msg2 = await ws2.receive_json()
            assert msg1["type"] == "new_message"
            assert msg2["type"] == "new_message"

# 场景4: 在线状态同步
async def test_online_status_sync():
    """测试在线状态变更通知。"""
    token1 = create_jwt_token(user1_id)
    token2 = create_jwt_token(user2_id)

    async with websocket_client(f"/ws?token={token1}") as ws1:
        await ws1.receive_json()

        # User2上线
        async with websocket_client(f"/ws?token={token2}") as ws2:
            await ws2.receive_json()

            # User1应该收到User2上线通知
            status_msg = await ws1.receive_json()
            assert status_msg["type"] == "status_change"
            assert status_msg["data"]["status"] == "online"
            assert status_msg["data"]["actor_id"] == str(user2_id)

        # User2断开连接
        # User1应该收到User2离线通知
        status_msg = await ws1.receive_json()
        assert status_msg["type"] == "status_change"
        assert status_msg["data"]["status"] == "offline"

# 场景5: 消息送达确认
async def test_message_acknowledgement():
    """测试消息送达确认。"""
    token = create_jwt_token(user_id)

    async with websocket_client(f"/ws?token={token}") as ws:
        await ws.receive_json()

        # 接收消息
        message = await ws.receive_json()
        assert message["type"] == "new_message"
        message_id = message["data"]["message_id"]

        # 发送确认
        await ws.send_json({
            "type": "ack",
            "message_id": message_id
        })

        # 验证日志记录（实际应用中可能更新数据库）
        # ...
```

## ✅ 验收标准

- [ ] 消息发送后实时推送给在线成员
- [ ] 离线用户不会收到实时推送
- [ ] 支持多设备同时推送
- [ ] 发送者可以选择是否接收自己的消息
- [ ] 在线状态变更实时通知
- [ ] 消息送达确认机制工作正常
- [ ] 推送失败有日志记录
- [ ] 事件系统正常工作
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 代码符合编码规范

## 🔧 技术要点

### 1. 事件驱动架构

```
REST API (发送消息)
    ↓
持久化到数据库
    ↓
发布MessageEvent
    ↓
EventBus分发
    ↓
MessageSentEventHandler
    ↓
MessagePushService
    ↓
WebSocket推送
```

### 2. 推送消息格式

**新消息推送**:
```json
{
  "type": "new_message",
  "data": {
    "message_id": "uuid",
    "conversation_id": "uuid",
    "sender": {
      "actor_type": "user",
      "actor_id": "uuid"
    },
    "message_type": "text",
    "content": "Hello!",
    "metadata": {},
    "created_at": "2026-03-17T..."
  }
}
```

**在线状态变更**:
```json
{
  "type": "status_change",
  "data": {
    "actor_type": "user",
    "actor_id": "uuid",
    "status": "online",
    "timestamp": "2026-03-17T..."
  }
}
```

**消息送达确认**:
```json
{
  "type": "ack",
  "message_id": "uuid"
}
```

### 3. 异步推送

使用`asyncio.gather`并行推送到多个连接：
```python
await asyncio.gather(
    *[ws.send_json(message) for ws in connections],
    return_exceptions=True
)
```

### 4. 推送统计

记录推送结果用于监控：
```python
{
    "success": 5,   # 成功推送数
    "failed": 1,    # 失败数
    "offline": 3    # 离线用户数
}
```

### 5. 事件总线扩展

当前使用内存EventBus，后续可以扩展为：
- Redis Pub/Sub（分布式）
- RabbitMQ（可靠性）
- Kafka（高吞吐）

### 6. 性能优化

- 使用异步推送不阻塞API响应
- 批量推送减少网络开销
- 连接池复用WebSocket连接
- 推送失败不影响消息持久化

## 🔜 下一步

完成迭代10后，进入**迭代11: Agent触发器**，实现Agent主动消息机制。

## 📊 预期成果

完成本迭代后，系统将具备：
- ✅ 完整的实时消息推送
- ✅ 事件驱动架构
- ✅ 在线状态同步
- ✅ 多设备推送支持
- ✅ 消息送达确认
- ✅ 推送统计和监控
- ✅ 完整的测试覆盖
- ✅ 为Agent主动消息打下基础

---

**创建日期**: 2026-03-17
**文档版本**: v1.0
