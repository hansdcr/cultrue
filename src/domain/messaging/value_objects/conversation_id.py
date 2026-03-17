"""Conversation ID value object."""
from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ConversationId:
    """会话ID值对象。"""
    value: UUID

    @classmethod
    def generate(cls) -> "ConversationId":
        """生成新的会话ID。

        Returns:
            ConversationId实例
        """
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> "ConversationId":
        """从字符串创建会话ID。

        Args:
            id_str: UUID字符串

        Returns:
            ConversationId实例
        """
        return cls(value=UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)
