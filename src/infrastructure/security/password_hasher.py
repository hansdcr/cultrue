"""密码加密服务。

使用bcrypt算法对密码进行加密和验证。
"""

from passlib.context import CryptContext


class PasswordHasher:
    """密码加密器。

    使用bcrypt算法对密码进行单向加密，并提供密码验证功能。
    """

    def __init__(self) -> None:
        """初始化密码加密器。"""
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """加密密码。

        Args:
            password: 明文密码

        Returns:
            加密后的密码哈希值
        """
        return self._pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码。

        Args:
            plain_password: 明文密码
            hashed_password: 加密后的密码哈希值

        Returns:
            密码是否匹配
        """
        return self._pwd_context.verify(plain_password, hashed_password)


# 创建全局实例
password_hasher = PasswordHasher()
