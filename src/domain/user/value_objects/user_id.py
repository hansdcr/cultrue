"""UserId值对象。

封装用户ID，确保ID的有效性。
"""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class UserId:
    """用户ID值对象。

    使用UUID作为用户的唯一标识符。
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        """验证用户ID。

        Raises:
            ValueError: 如果ID无效
        """
        if not isinstance(self.value, uuid.UUID):
            raise ValueError("User ID must be a UUID")

    @classmethod
    def generate(cls) -> "UserId":
        """生成新的用户ID。

        Returns:
            新的UserId实例
        """
        return cls(value=uuid.uuid4())

    @classmethod
    def from_string(cls, id_string: str) -> "UserId":
        """从字符串创建UserId。

        Args:
            id_string: UUID字符串

        Returns:
            UserId实例

        Raises:
            ValueError: 如果字符串不是有效的UUID
        """
        try:
            return cls(value=uuid.UUID(id_string))
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid UUID string: {id_string}") from e

    def __str__(self) -> str:
        """返回字符串表示。

        Returns:
            UUID字符串
        """
        return str(self.value)

    def __eq__(self, other: object) -> bool:
        """比较两个UserId是否相等。

        Args:
            other: 另一个对象

        Returns:
            是否相等
        """
        if not isinstance(other, UserId):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        """返回哈希值。

        Returns:
            哈希值
        """
        return hash(self.value)
