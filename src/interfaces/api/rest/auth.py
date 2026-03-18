"""认证API路由。

提供用户注册、登录、登出和刷新token的API端点。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.user.commands.login_command import (
    LoginCommand,
    LoginCommandHandler,
)
from src.application.user.commands.register_user_command import (
    RegisterUserCommand,
    RegisterUserCommandHandler,
)
from src.application.agent.commands.agent_login_command import (
    AgentLoginCommand,
    AgentLoginCommandHandler,
)
from src.domain.shared.exceptions import DomainException
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories.postgres_user_repository import (
    PostgresUserRepository,
)
from src.infrastructure.persistence.repositories.postgres_agent_repository import (
    PostgresAgentRepository,
)
from src.infrastructure.security.jwt_service import (
    JWTExpiredError,
    JWTInvalidError,
    jwt_service,
)
from src.interfaces.api.schemas.auth_schema import (
    AgentLoginRequest,
    AgentLoginResponse,
    AgentResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from src.interfaces.api.schemas.response import ApiResponse

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post(
    "/register",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="注册新用户账户",
)
async def register(
    request: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[UserResponse]:
    """用户注册。

    Args:
        request: 注册请求
        db: 数据库会话

    Returns:
        用户信息

    Raises:
        HTTPException: 如果用户名或邮箱已存在
    """
    try:
        # 创建仓储和命令处理器
        user_repository = PostgresUserRepository(db)
        handler = RegisterUserCommandHandler(user_repository)

        # 创建命令
        command = RegisterUserCommand(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
        )

        # 执行命令
        user_dto = await handler.handle(command)

        # 提交事务
        await db.commit()

        # 返回响应
        return ApiResponse.success(
            data=UserResponse(**user_dto.__dict__),
            message="User registered successfully",
        )

    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except DomainException as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/login",
    response_model=ApiResponse[LoginResponse],
    summary="用户登录",
    description="用户登录并获取访问令牌",
)
async def login(
    request: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[LoginResponse]:
    """用户登录。

    Args:
        request: 登录请求
        db: 数据库会话

    Returns:
        登录响应（包含用户信息和token）

    Raises:
        HTTPException: 如果邮箱或密码错误
    """
    try:
        # 创建仓储和命令处理器
        user_repository = PostgresUserRepository(db)
        handler = LoginCommandHandler(user_repository)

        # 创建命令
        command = LoginCommand(
            email=request.email,
            password=request.password,
        )

        # 执行命令
        login_result = await handler.handle(command)

        # 提交事务（更新last_login_at）
        await db.commit()

        # 返回响应
        return ApiResponse.success(
            data=LoginResponse(
                user=UserResponse(**login_result.user.__dict__),
                access_token=login_result.access_token,
                refresh_token=login_result.refresh_token,
                token_type=login_result.token_type,
            ),
            message="Login successful",
        )

    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    summary="刷新Token",
    description="使用刷新令牌获取新的访问令牌",
)
async def refresh_token(
    request: RefreshTokenRequest,
) -> ApiResponse[TokenResponse]:
    """刷新Token。

    Args:
        request: 刷新Token请求

    Returns:
        新的Token

    Raises:
        HTTPException: 如果刷新令牌无效或已过期
    """
    try:
        # 验证刷新令牌
        jwt_service.verify_token(request.refresh_token, token_type="refresh")

        # 从刷新令牌中获取用户ID
        user_id = jwt_service.get_user_id_from_token(request.refresh_token)

        # 生成新的访问令牌和刷新令牌
        new_access_token = jwt_service.create_access_token(user_id)
        new_refresh_token = jwt_service.create_refresh_token(user_id)

        # 返回响应
        return ApiResponse.success(
            data=TokenResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
            ),
            message="Token refreshed successfully",
        )

    except (JWTExpiredError, JWTInvalidError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/logout",
    response_model=ApiResponse[None],
    summary="用户登出",
    description="用户登出（客户端需要删除本地token）",
)
async def logout() -> ApiResponse[None]:
    """用户登出。

    注意：由于使用JWT，服务端无法主动使token失效。
    客户端需要删除本地存储的token。

    Returns:
        成功响应
    """
    return ApiResponse.success(
        data=None,
        message="Logout successful. Please delete your local tokens.",
    )


@router.post(
    "/agent-login",
    response_model=ApiResponse[AgentLoginResponse],
    summary="Agent登录",
    description="Agent通过 agent_id + api_key 登录，获取JWT Token",
)
async def agent_login(
    request: AgentLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[AgentLoginResponse]:
    """Agent登录。"""
    try:
        agent_repository = PostgresAgentRepository(db)
        handler = AgentLoginCommandHandler(agent_repository)
        command = AgentLoginCommand(
            agent_id=request.agent_id,
            api_key=request.api_key,
        )
        result = await handler.handle(command)

        return ApiResponse.success(
            data=AgentLoginResponse(
                agent=AgentResponse(
                    id=result.agent.id,
                    agent_id=result.agent.agent_id,
                    name=result.agent.name,
                    avatar=result.agent.avatar,
                    description=result.agent.description,
                    is_active=result.agent.is_active,
                ),
                access_token=result.access_token,
                refresh_token=result.refresh_token,
                token_type=result.token_type,
            ),
            message="Agent login successful",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
