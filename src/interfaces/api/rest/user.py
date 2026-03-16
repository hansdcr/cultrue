"""用户API路由。

提供用户信息查询和更新的API端点。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.user.commands.update_user_command import (
    UpdateUserCommand,
    UpdateUserCommandHandler,
)
from src.application.user.queries.get_user_query import (
    GetUserQuery,
    GetUserQueryHandler,
)
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories.postgres_user_repository import (
    PostgresUserRepository,
)
from src.interfaces.api.dependencies import CurrentActiveUser
from src.interfaces.api.schemas.response import ApiResponse
from src.interfaces.api.schemas.user_schema import UpdateUserRequest, UserResponse

router = APIRouter(prefix="/api/users", tags=["用户"])


@router.get("/test-auth")
async def test_auth(request: Request):
    """测试认证中间件。"""
    user_id = getattr(request.state, "user_id", None)
    authenticated = getattr(request.state, "authenticated", False)
    return {
        "user_id": user_id,
        "authenticated": authenticated,
        "has_authorization": "Authorization" in request.headers,
    }


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息",
)
async def get_current_user(
    current_user: CurrentActiveUser,
) -> ApiResponse[UserResponse]:
    """获取当前用户信息。

    Args:
        current_user: 当前用户（由依赖注入提供）

    Returns:
        当前用户信息
    """
    return ApiResponse.success(
        data=UserResponse(
            id=str(current_user.id),
            username=current_user.username,
            email=current_user.email,
            full_name=current_user.full_name,
            avatar_url=current_user.avatar_url,
            bio=current_user.bio,
            wallet_balance=current_user.wallet_balance,
            is_active=current_user.is_active,
            is_verified=current_user.is_verified,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
            last_login_at=current_user.last_login_at,
        ),
        message="User retrieved successfully",
    )


@router.put(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="更新当前用户信息",
    description="更新当前登录用户的资料信息",
)
async def update_current_user(
    request: UpdateUserRequest,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[UserResponse]:
    """更新当前用户信息。

    Args:
        request: 更新用户请求
        current_user: 当前用户（由依赖注入提供）
        db: 数据库会话

    Returns:
        更新后的用户信息

    Raises:
        HTTPException: 如果更新失败
    """
    try:
        # 创建仓储和命令处理器
        user_repository = PostgresUserRepository(db)
        handler = UpdateUserCommandHandler(user_repository)

        # 创建命令
        command = UpdateUserCommand(
            user_id=str(current_user.id),
            full_name=request.full_name,
            avatar_url=request.avatar_url,
            bio=request.bio,
        )

        # 执行命令
        user_dto = await handler.handle(command)

        # 提交事务
        await db.commit()

        # 返回响应
        return ApiResponse.success(
            data=UserResponse(**user_dto.__dict__),
            message="User updated successfully",
        )

    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    summary="获取指定用户信息",
    description="根据用户ID获取用户的详细信息",
)
async def get_user_by_id(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[UserResponse]:
    """获取指定用户信息。

    Args:
        user_id: 用户ID
        db: 数据库会话

    Returns:
        用户信息

    Raises:
        HTTPException: 如果用户不存在
    """
    try:
        # 创建仓储和查询处理器
        user_repository = PostgresUserRepository(db)
        handler = GetUserQueryHandler(user_repository)

        # 创建查询
        query = GetUserQuery(user_id=user_id)

        # 执行查询
        user_dto = await handler.handle(query)

        # 返回响应
        return ApiResponse.success(
            data=UserResponse(**user_dto.__dict__),
            message="User retrieved successfully",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
