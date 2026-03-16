"""PostgreSQL用户仓储实现。

实现UserRepository接口，处理用户数据的持久化。
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.user.entities.user import User
from src.domain.user.repositories.user_repository import UserRepository
from src.domain.user.value_objects.email import Email
from src.domain.user.value_objects.user_id import UserId
from ..models.user_model import UserModel


class PostgresUserRepository(UserRepository):
    """PostgreSQL用户仓储实现。"""

    def __init__(self, session: AsyncSession) -> None:
        """初始化仓储。

        Args:
            session: 数据库会话
        """
        self._session = session

    async def save(self, user: User) -> None:
        """保存用户。

        Args:
            user: 用户实体
        """
        user_model = self._to_model(user)
        self._session.add(user_model)
        await self._session.flush()

    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        """根据ID查找用户。

        Args:
            user_id: 用户ID

        Returns:
            用户实体，如果不存在则返回None
        """
        stmt = select(UserModel).where(UserModel.id == user_id.value)
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()

        if not user_model:
            return None

        return self._to_entity(user_model)

    async def find_by_email(self, email: Email) -> Optional[User]:
        """根据邮箱查找用户。

        Args:
            email: 邮箱

        Returns:
            用户实体，如果不存在则返回None
        """
        stmt = select(UserModel).where(UserModel.email == str(email))
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()

        if not user_model:
            return None

        return self._to_entity(user_model)

    async def find_by_username(self, username: str) -> Optional[User]:
        """根据用户名查找用户。

        Args:
            username: 用户名

        Returns:
            用户实体，如果不存在则返回None
        """
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()

        if not user_model:
            return None

        return self._to_entity(user_model)

    async def exists_by_email(self, email: Email) -> bool:
        """检查邮箱是否已存在。

        Args:
            email: 邮箱

        Returns:
            是否存在
        """
        stmt = select(UserModel.id).where(UserModel.email == str(email))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def exists_by_username(self, username: str) -> bool:
        """检查用户名是否已存在。

        Args:
            username: 用户名

        Returns:
            是否存在
        """
        stmt = select(UserModel.id).where(UserModel.username == username)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def delete(self, user_id: UserId) -> None:
        """删除用户。

        Args:
            user_id: 用户ID
        """
        stmt = select(UserModel).where(UserModel.id == user_id.value)
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()

        if user_model:
            await self._session.delete(user_model)
            await self._session.flush()

    async def update(self, user: User) -> None:
        """更新用户。

        Args:
            user: 用户实体
        """
        stmt = select(UserModel).where(UserModel.id == user.id.value)
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()

        if user_model:
            # 更新模型字段
            user_model.username = user.username
            user_model.email = str(user.email)
            user_model.password_hash = user.password_hash
            user_model.full_name = user.full_name
            user_model.avatar_url = user.avatar_url
            user_model.bio = user.bio
            user_model.wallet_balance = user.wallet_balance
            user_model.is_active = user.is_active
            user_model.is_verified = user.is_verified
            user_model.updated_at = user.updated_at
            user_model.last_login_at = user.last_login_at

            await self._session.flush()

    def _to_entity(self, model: UserModel) -> User:
        """将数据库模型转换为领域实体。

        Args:
            model: 数据库模型

        Returns:
            用户实体
        """
        return User(
            id=UserId(value=model.id),
            username=model.username,
            email=Email(value=model.email),
            password_hash=model.password_hash,
            full_name=model.full_name,
            avatar_url=model.avatar_url,
            bio=model.bio,
            wallet_balance=model.wallet_balance,
            is_active=model.is_active,
            is_verified=model.is_verified,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login_at=model.last_login_at,
        )

    def _to_model(self, entity: User) -> UserModel:
        """将领域实体转换为数据库模型。

        Args:
            entity: 用户实体

        Returns:
            数据库模型
        """
        return UserModel(
            id=entity.id.value,
            username=entity.username,
            email=str(entity.email),
            password_hash=entity.password_hash,
            full_name=entity.full_name,
            avatar_url=entity.avatar_url,
            bio=entity.bio,
            wallet_balance=entity.wallet_balance,
            is_active=entity.is_active,
            is_verified=entity.is_verified,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            last_login_at=entity.last_login_at,
        )
