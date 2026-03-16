"""用户DTO（数据传输对象）。

用于在应用层和接口层之间传输用户数据。
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class UserDTO:
    """用户数据传输对象。

    用于在不同层之间传输用户数据，避免直接暴露领域实体。
    """

    id: str
    username: str
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    wallet_balance: Decimal
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]

    @classmethod
    def from_entity(cls, user: "User") -> "UserDTO":  # type: ignore
        """从User实体创建DTO。

        Args:
            user: User实体

        Returns:
            UserDTO实例
        """
        return cls(
            id=str(user.id),
            username=user.username,
            email=str(user.email),
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            bio=user.bio,
            wallet_balance=user.wallet_balance,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
        )
