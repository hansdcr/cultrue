"""Connection entity."""
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.domain.shared.value_objects.actor import Actor
from src.domain.realtime.enums.connection_status import ConnectionStatus


@dataclass
class Connection:
    """WebSocket连接实体。"""
    id: UUID
    actor: Actor
    status: ConnectionStatus
    connected_at: datetime
    last_heartbeat_at: datetime
    metadata: dict

    def is_alive(self, timeout_seconds: int = 60) -> bool:
        """检查连接是否存活。

        Args:
            timeout_seconds: 超时时间（秒）

        Returns:
            如果连接存活返回True，否则返回False
        """
        if self.status != ConnectionStatus.CONNECTED:
            return False
        elapsed = datetime.now(timezone.utc) - self.last_heartbeat_at
        return elapsed.total_seconds() < timeout_seconds

    def update_heartbeat(self) -> None:
        """更新心跳时间。"""
        self.last_heartbeat_at = datetime.now(timezone.utc)

    @classmethod
    def create(cls, actor: Actor, metadata: dict = None) -> "Connection":
        """创建新连接。

        Args:
            actor: Actor值对象
            metadata: 连接元数据

        Returns:
            Connection实例
        """
        now = datetime.now(timezone.utc)
        return cls(
            id=uuid4(),
            actor=actor,
            status=ConnectionStatus.CONNECTING,
            connected_at=now,
            last_heartbeat_at=now,
            metadata=metadata or {}
        )
