"""Email值对象。

封装邮箱地址，确保邮箱格式的有效性。
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """邮箱值对象。

    验证并封装邮箱地址。
    """

    value: str

    # 邮箱正则表达式
    EMAIL_REGEX = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    def __post_init__(self) -> None:
        """验证邮箱格式。

        Raises:
            ValueError: 如果邮箱格式无效
        """
        if not isinstance(self.value, str):
            raise ValueError("Email must be a string")

        if not self.value:
            raise ValueError("Email cannot be empty")

        if len(self.value) > 255:
            raise ValueError("Email is too long (max 255 characters)")

        if not self.EMAIL_REGEX.match(self.value):
            raise ValueError(f"Invalid email format: {self.value}")

    @classmethod
    def from_string(cls, email_string: str) -> "Email":
        """从字符串创建Email。

        Args:
            email_string: 邮箱字符串

        Returns:
            Email实例

        Raises:
            ValueError: 如果邮箱格式无效
        """
        # 转换为小写并去除空格
        normalized_email = email_string.strip().lower()
        return cls(value=normalized_email)

    def __str__(self) -> str:
        """返回字符串表示。

        Returns:
            邮箱字符串
        """
        return self.value

    def __eq__(self, other: object) -> bool:
        """比较两个Email是否相等。

        Args:
            other: 另一个对象

        Returns:
            是否相等
        """
        if not isinstance(other, Email):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        """返回哈希值。

        Returns:
            哈希值
        """
        return hash(self.value)
