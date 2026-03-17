"""Connection manager service."""
import asyncio
import logging
from typing import Dict, Set

from fastapi import WebSocket

from src.domain.shared.value_objects.actor import Actor
from src.domain.realtime.entities.connection import Connection
from src.domain.realtime.enums.connection_status import ConnectionStatus

logger = logging.getLogger(__name__)


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
        """注册新连接。

        Args:
            websocket: WebSocket连接
            actor: Actor值对象
            metadata: 连接元数据

        Returns:
            Connection实例
        """
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

            logger.info(f"Connection established: {actor_key}, connection_id={connection.id}")
            return connection

    async def disconnect(self, websocket: WebSocket) -> None:
        """注销连接。

        Args:
            websocket: WebSocket连接
        """
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

            logger.info(f"Connection disconnected: {actor_key}, connection_id={connection.id}")

    async def update_heartbeat(self, websocket: WebSocket) -> None:
        """更新连接心跳。

        Args:
            websocket: WebSocket连接
        """
        if websocket in self._connection_entities:
            self._connection_entities[websocket].update_heartbeat()

    def get_connections(self, actor: Actor) -> Set[WebSocket]:
        """获取Actor的所有连接（支持多设备）。

        Args:
            actor: Actor值对象

        Returns:
            WebSocket连接集合
        """
        actor_key = self._get_actor_key(actor)
        return self._connections.get(actor_key, set()).copy()

    def is_online(self, actor: Actor) -> bool:
        """检查Actor是否在线。

        Args:
            actor: Actor值对象

        Returns:
            如果在线返回True，否则返回False
        """
        actor_key = self._get_actor_key(actor)
        return actor_key in self._connections and len(self._connections[actor_key]) > 0

    async def cleanup_dead_connections(self, timeout_seconds: int = 60) -> int:
        """清理僵尸连接。

        Args:
            timeout_seconds: 超时时间（秒）

        Returns:
            清理的连接数量
        """
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
            except Exception as e:
                logger.warning(f"Failed to close websocket: {e}")

        if dead_connections:
            logger.info(f"Cleaned up {len(dead_connections)} dead connections")

        return len(dead_connections)

    def _get_actor_key(self, actor: Actor) -> str:
        """生成Actor的唯一键。

        Args:
            actor: Actor值对象

        Returns:
            Actor唯一键字符串
        """
        return f"{actor.actor_type.value}:{actor.actor_id}"
