"""FastAPI依赖注入。

提供认证、数据库等依赖。
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models import UserModel
from src.domain.shared.value_objects.actor import Actor


async def get_current_actor(request: Request) -> Actor:
    """获取当前Actor（User或Agent）。

    从request.state中获取actor（由统一认证中间件注入）。

    Args:
        request: FastAPI请求对象

    Returns:
        Actor值对象

    Raises:
        HTTPException: 如果未认证
    """
    actor = getattr(request.state, "actor", None)

    if not actor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer or ApiKey"},
        )

    return actor


async def get_current_user_id(request: Request) -> str:
    """获取当前用户ID。

    从request.state中获取用户ID（由AuthMiddleware注入）。

    Args:
        request: FastAPI请求对象

    Returns:
        用户ID

    Raises:
        HTTPException: 如果用户未认证
    """
    user_id = getattr(request.state, "user_id", None)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def get_current_user(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserModel:
    """获取当前用户。

    从数据库中查询当前用户的完整信息。

    Args:
        user_id: 用户ID（由get_current_user_id依赖提供）
        db: 数据库会话（由get_db依赖提供）

    Returns:
        用户模型对象

    Raises:
        HTTPException: 如果用户不存在
    """
    # 将字符串user_id转换为UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )

    stmt = select(UserModel).where(UserModel.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


async def get_current_active_user(
    user: Annotated[UserModel, Depends(get_current_user)],
) -> UserModel:
    """获取当前活跃用户。

    验证用户是否处于活跃状态。

    Args:
        user: 用户模型对象（由get_current_user依赖提供）

    Returns:
        用户模型对象

    Raises:
        HTTPException: 如果用户未激活
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not active",
        )

    return user


async def require_admin(
    user: Annotated[UserModel, Depends(get_current_active_user)],
) -> UserModel:
    """验证当前用户是否为管理员。

    Args:
        user: 用户模型对象（由get_current_active_user依赖提供）

    Returns:
        用户模型对象

    Raises:
        HTTPException: 如果用户不是管理员
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator permission required",
        )

    return user


# 类型别名，方便在路由中使用
CurrentActor = Annotated[Actor, Depends(get_current_actor)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
CurrentUser = Annotated[UserModel, Depends(get_current_user)]
CurrentActiveUser = Annotated[UserModel, Depends(get_current_active_user)]
CurrentAdmin = Annotated[UserModel, Depends(require_admin)]
