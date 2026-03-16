"""UserRepository接口。

定义用户仓储的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..entities.user import User
from ..value_objects.email import Email
from ..value_objects.user_id import UserId


class UserRepository(ABC):
    """用户仓储接口。

    定义用户数据持久化的抽象操作。
    """

    @abstractmethod
    async def save(self, user: User) -> None:
        """保存用户。

        Args:
            user: 用户实体
        """
        pass

    @abstractmethod
    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        """根据ID查找用户。

        Args:
            user_id: 用户ID

        Returns:
            用户实体，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def find_by_email(self, email: Email) -> Optional[User]:
        """根据邮箱查找用户。

        Args:
            email: 邮箱

        Returns:
            用户实体，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        """根据用户名查找用户。

        Args:
            username: 用户名

        Returns:
            用户实体，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def exists_by_email(self, email: Email) -> bool:
        """检查邮箱是否已存在。

        Args:
            email: 邮箱

        Returns:
            是否存在
        """
        pass

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """检查用户名是否已存在。

        Args:
            username: 用户名

        Returns:
            是否存在
        """
        pass

    @abstractmethod
    async def delete(self, user_id: UserId) -> None:
        """删除用户。

        Args:
            user_id: 用户ID
        """
        pass

    @abstractmethod
    async def update(self, user: User) -> None:
        """更新用户。

        Args:
            user: 用户实体
        """
        pass
