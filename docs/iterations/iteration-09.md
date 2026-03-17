# 迭代9: WebSocket-基础

> 实现WebSocket连接管理和认证机制

## 📋 迭代信息

- **迭代编号**: 9
- **预计时间**: 1天
- **当前状态**: ⬜ 未开始
- **依赖迭代**: 迭代8 ✅
- **开始日期**: 待定

## 🎯 迭代目标

实现WebSocket连接的完整生命周期管理，包括连接建立、认证、心跳保活、断线重连和连接关闭。为后续的实时消息推送打下基础。

## 💡 设计理念

**统一认证架构**：
- 支持User JWT认证和Agent API Key认证
- 复用Actor值对象统一抽象
- 连接管理器维护Actor到WebSocket的映射

**高可用设计**：
- 心跳机制检测连接状态
- 自动清理僵尸连接
- 支持客户端断线重连
- 连接状态持久化（可选）

## 📝 任务清单

### 1. WebSocket连接模型

**任务**:
- [ ] 创建ConnectionId值对象
- [ ] 创建Connection实体
- [ ] 创建ConnectionStatus枚举
- [ ] 设计连接元数据结构

**交付物**:
- `src/domain/realtime/value_objects/connection_id.py`
- `src/domain/realtime/entities/connection.py`
- `src/domain/realtime/enums/connection_status.py`

**设计要点**:
```python
from src.domain.shared.value_objects.actor import Actor

class ConnectionStatus(str, Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

@dataclass
class Connection:
    """WebSocket连接实体。"""
    id: UUID
    actor: Actor  # 使用Actor值对象
    status: ConnectionStatus
    connected_at: datetime
    last_heartbeat_at: datetime
    metadata: dict  # 存储设备信息、IP等

    def is_alive(self, timeout_seconds: int = 60) -> bool:
        """检查连接是否存活。"""
        if self.status != ConnectionStatus.CONNECTED:
            return False
        elapsed = datetime.now(timezone.utc) - self.last_heartbeat_at
        return elapsed.total_seconds() < timeout_seconds

    def update_heartbeat(self) -> None:
        """更新心跳时间。"""
        self.last_heartbeat_at = datetime.now(timezone.utc)

    @classmethod
    def create(cls, actor: Actor, metadata: dict = None) -> "Connection":
        """创建新连接。"""
        now = datetime.now(timezone.utc)
        return cls(
            id=uuid4(),
            actor=actor,
            status=ConnectionStatus.CONNECTING,
            connected_at=now,
            last_heartbeat_at=now,
            metadata=metadata or {}
        )
```

### 2. WebSocket连接管理器

**任务**:
- [ ] 创建ConnectionManager服务
- [ ] 实现连接注册和注销
- [ ] 实现Actor到WebSocket的映射
- [ ] 实现心跳检测机制
- [ ] 实现僵尸连接清理

**交付物**:
- `src/application/realtime/services/connection_manager.py`

**设计要点**:
```python
from fastapi import WebSocket
from typing import Dict, Set
from src.domain.shared.value_objects.actor import Actor

class ConnectionManager:
    """WebSocket连接管理器。"""

    def __init__(self):
        # Actor -> Set[WebSocket] (支持多设备登录)
        self._connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> Connection实体
        self._connection_entities: Dict[WebSocket, Connection] = {}
        # 连接锁
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        actor: Actor,
        metadata: dict = None
    ) -> Connection:
        """注册新连接。"""
        async with self._lock:
            # 创建连接实体
            connection = Connection.create(actor, metadata)

            # 存储映射
            actor_key = self._get_actor_key(actor)
            if actor_key not in self._connections:
                self._connections[actor_key] = set()
            self._connections[actor_key].add(websocket)
            self._connection_entities[websocket] = connection

            # 更新状态
            connection.status = ConnectionStatus.CONNECTED

            return connection

    async def disconnect(self, websocket: WebSocket) -> None:
        """注销连接。"""
        async with self._lock:
            if websocket not in self._connection_entities:
                return

            connection = self._connection_entities[websocket]
            actor_key = self._get_actor_key(connection.actor)

            # 移除映射
            if actor_key in self._connections:
                self._connections[actor_key].discard(websocket)
                if not self._connections[actor_key]:
                    del self._connections[actor_key]

            del self._connection_entities[websocket]
            connection.status = ConnectionStatus.DISCONNECTED

    async def update_heartbeat(self, websocket: WebSocket) -> None:
        """更新连接心跳。"""
        if websocket in self._connection_entities:
            self._connection_entities[websocket].update_heartbeat()

    def get_connections(self, actor: Actor) -> Set[WebSocket]:
        """获取Actor的所有连接（支持多设备）。"""
        actor_key = self._get_actor_key(actor)
        return self._connections.get(actor_key, set()).copy()

    def is_online(self, actor: Actor) -> bool:
        """检查Actor是否在线。"""
        actor_key = self._get_actor_key(actor)
        return actor_key in self._connections and len(self._connections[actor_key]) > 0

    async def cleanup_dead_connections(self, timeout_seconds: int = 60) -> int:
        """清理僵尸连接。"""
        dead_connections = []

        async with self._lock:
            for websocket, connection in self._connection_entities.items():
                if not connection.is_alive(timeout_seconds):
                    dead_connections.append(websocket)

        # 清理死连接
        for websocket in dead_connections:
            await self.disconnect(websocket)
            try:
                await websocket.close(code=1000, reason="Connection timeout")
            except:
                pass

        return len(dead_connections)

    def _get_actor_key(self, actor: Actor) -> str:
        """生成Actor的唯一键。"""
        return f"{actor.actor_type.value}:{actor.actor_id}"
```

### 3. WebSocket认证中间件

**任务**:
- [ ] 创建WebSocket认证函数
- [ ] 支持JWT token认证（User）
- [ ] 支持API Key认证（Agent）
- [ ] 处理认证失败场景

**交付物**:
- `src/interfaces/websocket/auth.py`

**设计要点**:
```python
from fastapi import WebSocket, WebSocketDisconnect
from src.domain.shared.value_objects.actor import Actor

async def authenticate_websocket(
    websocket: WebSocket,
    token: str = None,
    api_key: str = None
) -> Actor:
    """
    WebSocket连接认证。

    支持两种认证方式：
    1. token参数 - User JWT认证
    2. api_key参数 - Agent API Key认证
    """
    if token:
        # User JWT认证
        try:
            user_id = jwt_service.verify_token(token)
            return Actor.from_user(UUID(user_id))
        except Exception as e:
            await websocket.close(code=4001, reason="Invalid token")
            raise WebSocketDisconnect(code=4001, reason="Invalid token")

    elif api_key:
        # Agent API Key认证
        try:
            agent = await agent_repo.find_by_api_key(ApiKey(api_key))
            if agent and agent.verify_api_key(ApiKey(api_key)):
                return Actor.from_agent(agent.id)
            else:
                await websocket.close(code=4001, reason="Invalid API key")
                raise WebSocketDisconnect(code=4001, reason="Invalid API key")
        except Exception as e:
            await websocket.close(code=4001, reason="Authentication failed")
            raise WebSocketDisconnect(code=4001, reason="Authentication failed")

    else:
        await websocket.close(code=4000, reason="Missing credentials")
        raise WebSocketDisconnect(code=4000, reason="Missing credentials")
```

### 4. WebSocket端点实现

**任务**:
- [ ] 创建WebSocket路由
- [ ] 实现连接建立逻辑
- [ ] 实现心跳处理
- [ ] 实现消息接收和分发
- [ ] 实现连接关闭处理

**交付物**:
- `src/interfaces/websocket/endpoints.py`

**设计要点**:
```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None),
    api_key: str = Query(None),
    connection_manager: ConnectionManager = Depends(get_connection_manager)
):
    """
    WebSocket连接端点。

    连接URL示例：
    - User: ws://localhost:8000/ws?token=<jwt_token>
    - Agent: ws://localhost:8000/ws?api_key=<api_key>
    """
    # 1. 接受连接
    await websocket.accept()

    try:
        # 2. 认证
        actor = await authenticate_websocket(websocket, token, api_key)

        # 3. 注册连接
        metadata = {
            "user_agent": websocket.headers.get("user-agent"),
            "client_ip": websocket.client.host if websocket.client else None
        }
        connection = await connection_manager.connect(websocket, actor, metadata)

        # 4. 发送连接成功消息
        await websocket.send_json({
            "type": "connection_established",
            "data": {
                "connection_id": str(connection.id),
                "actor_type": actor.actor_type.value,
                "actor_id": str(actor.actor_id),
                "connected_at": connection.connected_at.isoformat()
            }
        })

        # 5. 消息循环
        while True:
            # 接收消息
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "ping":
                # 心跳响应
                await connection_manager.update_heartbeat(websocket)
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

            elif message_type == "message":
                # 消息发送（迭代10实现）
                pass

            else:
                # 未知消息类型
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })

    except WebSocketDisconnect:
        # 客户端断开连接
        pass
    except Exception as e:
        # 异常处理
        logger.error(f"WebSocket error: {e}")
    finally:
        # 6. 清理连接
        await connection_manager.disconnect(websocket)
```

### 5. 心跳和清理任务

**任务**:
- [ ] 创建后台任务调度器
- [ ] 实现定时心跳检测
- [ ] 实现僵尸连接清理
- [ ] 添加连接统计日志

**交付物**:
- `src/application/realtime/tasks/connection_cleanup.py`

**设计要点**:
```python
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class ConnectionCleanupTask:
    """连接清理后台任务。"""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        interval_seconds: int = 30,
        timeout_seconds: int = 60
    ):
        self.connection_manager = connection_manager
        self.interval_seconds = interval_seconds
        self.timeout_seconds = timeout_seconds
        self.scheduler = AsyncIOScheduler()

    async def cleanup(self) -> None:
        """执行清理任务。"""
        try:
            count = await self.connection_manager.cleanup_dead_connections(
                self.timeout_seconds
            )
            if count > 0:
                logger.info(f"Cleaned up {count} dead connections")
        except Exception as e:
            logger.error(f"Connection cleanup error: {e}")

    def start(self) -> None:
        """启动清理任务。"""
        self.scheduler.add_job(
            self.cleanup,
            'interval',
            seconds=self.interval_seconds
        )
        self.scheduler.start()
        logger.info(f"Connection cleanup task started (interval={self.interval_seconds}s)")

    def stop(self) -> None:
        """停止清理任务。"""
        self.scheduler.shutdown()
        logger.info("Connection cleanup task stopped")
```

### 6. 集成到main.py

**任务**:
- [ ] 注册WebSocket路由
- [ ] 启动连接清理任务
- [ ] 配置依赖注入
- [ ] 添加应用生命周期事件

**交付物**:
- 更新 `main.py`

**集成要点**:
```python
from src.interfaces.websocket import endpoints as ws_endpoints
from src.application.realtime.services.connection_manager import ConnectionManager
from src.application.realtime.tasks.connection_cleanup import ConnectionCleanupTask

# 全局连接管理器
connection_manager = ConnectionManager()
cleanup_task = None

@app.on_event("startup")
async def startup_event():
    """应用启动事件。"""
    global cleanup_task
    # 启动连接清理任务
    cleanup_task = ConnectionCleanupTask(connection_manager)
    cleanup_task.start()
    logger.info("WebSocket connection manager initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件。"""
    global cleanup_task
    if cleanup_task:
        cleanup_task.stop()
    logger.info("WebSocket connection manager shutdown")

# 注册WebSocket路由
app.include_router(ws_endpoints.router, tags=["websocket"])

# 依赖注入
def get_connection_manager() -> ConnectionManager:
    return connection_manager
```

### 7. 测试

**任务**:
- [ ] 编写ConnectionManager单元测试
- [ ] 编写WebSocket连接集成测试
- [ ] 测试认证流程
- [ ] 测试心跳机制
- [ ] 测试断线重连
- [ ] 测试多设备登录

**交付物**:
- `tests/unit/application/realtime/test_connection_manager.py`
- `tests/integration/test_websocket_connection.py`

**测试场景**:
```python
# 场景1: User WebSocket连接
async def test_user_websocket_connection():
    """测试User通过JWT连接WebSocket。"""
    token = create_jwt_token(user_id)
    async with websocket_client(f"/ws?token={token}") as ws:
        # 接收连接成功消息
        message = await ws.receive_json()
        assert message["type"] == "connection_established"
        assert message["data"]["actor_type"] == "user"

        # 发送心跳
        await ws.send_json({"type": "ping"})
        response = await ws.receive_json()
        assert response["type"] == "pong"

# 场景2: Agent WebSocket连接
async def test_agent_websocket_connection():
    """测试Agent通过API Key连接WebSocket。"""
    api_key = agent.api_key.value
    async with websocket_client(f"/ws?api_key={api_key}") as ws:
        message = await ws.receive_json()
        assert message["type"] == "connection_established"
        assert message["data"]["actor_type"] == "agent"

# 场景3: 认证失败
async def test_websocket_auth_failure():
    """测试WebSocket认证失败。"""
    with pytest.raises(WebSocketDisconnect):
        async with websocket_client("/ws?token=invalid") as ws:
            pass

# 场景4: 多设备登录
async def test_multiple_device_connections():
    """测试同一User多设备登录。"""
    token = create_jwt_token(user_id)

    async with websocket_client(f"/ws?token={token}") as ws1:
        async with websocket_client(f"/ws?token={token}") as ws2:
            # 两个连接都应该成功
            msg1 = await ws1.receive_json()
            msg2 = await ws2.receive_json()
            assert msg1["type"] == "connection_established"
            assert msg2["type"] == "connection_established"

            # 检查在线状态
            actor = Actor.from_user(user_id)
            assert connection_manager.is_online(actor)
            connections = connection_manager.get_connections(actor)
            assert len(connections) == 2

# 场景5: 心跳超时清理
async def test_heartbeat_timeout_cleanup():
    """测试心跳超时后连接被清理。"""
    token = create_jwt_token(user_id)

    async with websocket_client(f"/ws?token={token}") as ws:
        # 连接成功
        await ws.receive_json()

        # 等待超时
        await asyncio.sleep(65)  # 超过60秒超时

        # 执行清理
        count = await connection_manager.cleanup_dead_connections(timeout_seconds=60)
        assert count == 1

        # 检查连接已断开
        actor = Actor.from_user(user_id)
        assert not connection_manager.is_online(actor)
```

## ✅ 验收标准

- [ ] WebSocket连接可以成功建立
- [ ] User可以通过JWT token连接
- [ ] Agent可以通过API Key连接
- [ ] 认证失败时连接被拒绝
- [ ] 心跳机制正常工作
- [ ] 僵尸连接可以被自动清理
- [ ] 支持同一Actor多设备登录
- [ ] 连接断开时资源正确释放
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 代码符合编码规范

## 🔧 技术要点

### 1. WebSocket协议

FastAPI使用Starlette的WebSocket支持：
```python
from fastapi import WebSocket

# 接受连接
await websocket.accept()

# 发送JSON消息
await websocket.send_json({"type": "message", "data": {...}})

# 接收JSON消息
data = await websocket.receive_json()

# 关闭连接
await websocket.close(code=1000, reason="Normal closure")
```

### 2. 认证方式

**User认证（JWT）**：
```
ws://localhost:8000/ws?token=<jwt_token>
```

**Agent认证（API Key）**：
```
ws://localhost:8000/ws?api_key=<api_key>
```

### 3. 消息格式

统一的JSON消息格式：
```json
{
  "type": "message_type",
  "data": {...},
  "timestamp": "2026-03-17T..."
}
```

消息类型：
- `connection_established` - 连接建立
- `ping` / `pong` - 心跳
- `message` - 业务消息（迭代10）
- `error` - 错误消息

### 4. 心跳机制

**客户端发送**：
```json
{"type": "ping"}
```

**服务端响应**：
```json
{
  "type": "pong",
  "timestamp": "2026-03-17T10:30:00Z"
}
```

**超时检测**：
- 默认60秒无心跳视为连接超时
- 后台任务每30秒检查一次
- 超时连接自动关闭并清理

### 5. 多设备支持

使用`Dict[str, Set[WebSocket]]`支持同一Actor多设备登录：
```python
# Actor可以有多个WebSocket连接
connections = {
    "user:uuid1": {websocket1, websocket2},  # 两个设备
    "agent:uuid2": {websocket3}              # 一个设备
}
```

### 6. 连接状态管理

```python
# 检查在线状态
is_online = connection_manager.is_online(actor)

# 获取所有连接
connections = connection_manager.get_connections(actor)

# 向所有设备发送消息
for ws in connections:
    await ws.send_json(message)
```

### 7. 错误处理

```python
try:
    await websocket.send_json(message)
except WebSocketDisconnect:
    # 客户端断开
    await connection_manager.disconnect(websocket)
except Exception as e:
    # 其他错误
    logger.error(f"WebSocket error: {e}")
    await websocket.close(code=1011, reason="Internal error")
```

## 🔜 下一步

完成迭代9后，进入**迭代10: WebSocket-消息推送**，实现实时消息推送功能。

## 📊 预期成果

完成本迭代后，系统将具备：
- ✅ 完整的WebSocket连接管理
- ✅ 统一的User和Agent认证
- ✅ 心跳保活机制
- ✅ 自动清理僵尸连接
- ✅ 多设备登录支持
- ✅ 连接状态查询
- ✅ 完整的测试覆盖
- ✅ 为实时消息推送打下基础

---

**创建日期**: 2026-03-17
**文档版本**: v1.0
