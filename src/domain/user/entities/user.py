"""User实体。

用户领域实体，包含用户的核心业务逻辑。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from ..value_objects.email import Email
from ..value_objects.user_id import UserId


@dataclass
class User:
    """用户实体。

    代表系统中的一个用户，包含用户的所有属性和行为。
    """

    id: UserId
    username: str
    email: Email
    password_hash: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    wallet_balance: Decimal = field(default_factory=lambda: Decimal("0.00"))
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """验证用户实体。

        Raises:
            ValueError: 如果用户数据无效
        """
        self._validate()

    def _validate(self) -> None:
        """验证用户数据。

        Raises:
            ValueError: 如果用户数据无效
        """
        if not self.username:
            raise ValueError("Username cannot be empty")

        if len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters")

        if len(self.username) > 50:
            raise ValueError("Username is too long (max 50 characters)")

        if not self.password_hash:
            raise ValueError("Password hash cannot be empty")

        if self.wallet_balance < 0:
            raise ValueError("Wallet balance cannot be negative")

    @classmethod
    def create(
        cls,
        username: str,
        email: Email,
        password_hash: str,
        full_name: Optional[str] = None,
    ) -> "User":
        """创建新用户。

        Args:
            username: 用户名
            email: 邮箱
            password_hash: 密码哈希
            full_name: 全名（可选）

        Returns:
            新的User实例
        """
        return cls(
            id=UserId.generate(),
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
        )

    def update_profile(
        self,
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        bio: Optional[str] = None,
    ) -> None:
        """更新用户资料。

        Args:
            full_name: 全名
            avatar_url: 头像URL
            bio: 个人简介
        """
        if full_name is not None:
            self.full_name = full_name
        if avatar_url is not None:
            self.avatar_url = avatar_url
        if bio is not None:
            self.bio = bio
        self.updated_at = datetime.now(timezone.utc)

    def update_password(self, new_password_hash: str) -> None:
        """更新密码。

        Args:
            new_password_hash: 新密码哈希
        """
        if not new_password_hash:
            raise ValueError("Password hash cannot be empty")
        self.password_hash = new_password_hash
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_verified(self) -> None:
        """标记用户为已验证。"""
        self.is_verified = True
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """停用用户账户。"""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def activate(self) -> None:
        """激活用户账户。"""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def record_login(self) -> None:
        """记录用户登录。"""
        self.last_login_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def add_balance(self, amount: Decimal) -> None:
        """增加钱包余额。

        Args:
            amount: 增加的金额

        Raises:
            ValueError: 如果金额为负数
        """
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        self.wallet_balance += amount
        self.updated_at = datetime.now(timezone.utc)

    def deduct_balance(self, amount: Decimal) -> None:
        """扣除钱包余额。

        Args:
            amount: 扣除的金额

        Raises:
            ValueError: 如果金额为负数或余额不足
        """
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        if self.wallet_balance < amount:
            raise ValueError("Insufficient balance")
        self.wallet_balance -= amount
        self.updated_at = datetime.now(timezone.utc)

    def __eq__(self, other: object) -> bool:
        """比较两个User是否相等。

        Args:
            other: 另一个对象

        Returns:
            是否相等
        """
        if not isinstance(other, User):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """返回哈希值。

        Returns:
            哈希值
        """
        return hash(self.id)
