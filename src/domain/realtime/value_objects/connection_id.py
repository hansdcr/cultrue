"""Connection ID value object."""
from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ConnectionId:
    """连接ID值对象。"""
    value: UUID

    @classmethod
    def generate(cls) -> "ConnectionId":
        """生成新的连接ID。

        Returns:
            ConnectionId实例
        """
        return cls(value=uuid4())

    def __str__(self) -> str:
        """返回字符串表示。

        Returns:
            UUID字符串
        """
        return str(self.value)
