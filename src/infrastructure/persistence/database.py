"""数据库连接和会话管理模块。

提供异步数据库连接、会话管理和基础模型类。
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy声明式基类。

    所有数据库模型都应该继承此类。
    """
    pass


class DatabaseManager:
    """数据库管理器。

    负责创建和管理数据库引擎和会话。
    """

    def __init__(self, database_url: str, pool_size: int = 20, max_overflow: int = 10) -> None:
        """初始化数据库管理器。

        Args:
            database_url: 数据库连接URL
            pool_size: 连接池大小
            max_overflow: 连接池最大溢出数量
        """
        self.engine = create_async_engine(
            database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=False,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话。

        Yields:
            AsyncSession: 异步数据库会话
        """
        async with self.session_factory() as session:
            yield session

    async def close(self) -> None:
        """关闭数据库连接。"""
        await self.engine.dispose()


# 全局数据库管理器实例
_db_manager: DatabaseManager | None = None


def init_database(database_url: str, pool_size: int = 20, max_overflow: int = 10) -> None:
    """初始化全局数据库管理器。

    Args:
        database_url: 数据库连接URL
        pool_size: 连接池大小
        max_overflow: 连接池最大溢出数量
    """
    global _db_manager
    _db_manager = DatabaseManager(database_url, pool_size, max_overflow)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖注入函数。

    用于FastAPI的依赖注入。

    Yields:
        AsyncSession: 异步数据库会话

    Raises:
        RuntimeError: 如果数据库未初始化
    """
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    async for session in _db_manager.get_session():
        yield session


async def close_database() -> None:
    """关闭全局数据库连接。"""
    if _db_manager is not None:
        await _db_manager.close()


# 别名，方便使用
get_db = get_db_session
