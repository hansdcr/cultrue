"""Message ID value object."""
from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class MessageId:
    """消息ID值对象。"""
    value: UUID

    @classmethod
    def generate(cls) -> "MessageId":
        """生成新的消息ID。

        Returns:
            MessageId实例
        """
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> "MessageId":
        """从字符串创建消息ID。

        Args:
            id_str: UUID字符串

        Returns:
            MessageId实例
        """
        return cls(value=UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)
