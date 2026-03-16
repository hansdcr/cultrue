"""统一认证中间件。

支持User JWT和Agent API Key两种认证方式。
"""

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.agent.value_objects.api_key import ApiKey
from src.domain.shared.value_objects.actor import Actor
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.repositories.postgres_agent_repository import (
    PostgresAgentRepository,
)
from src.infrastructure.security.jwt_service import (
    JWTExpiredError,
    JWTInvalidError,
    jwt_service,
)
from src.interfaces.api.schemas.response import ApiResponse


class UnifiedAuthMiddleware(BaseHTTPMiddleware):
    """统一认证中间件。

    支持两种认证方式：
    1. User JWT认证：Authorization: Bearer <token>
    2. Agent API Key认证：Authorization: ApiKey <api_key>
    """

    # 不需要认证的路径
    EXCLUDED_PATHS = [
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/auth/register",
        "/api/auth/login",
        "/api/auth/refresh",
        "/api/agents/register",  # Agent自主注册
        "/health",
    ]

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """处理请求。

        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理器

        Returns:
            响应对象
        """
        # 检查是否是不需要认证的路径
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        # 提取Authorization header
        authorization = request.headers.get("Authorization")

        if not authorization:
            # 如果没有认证信息，继续处理请求（由路由的依赖来决定是否需要认证）
            return await call_next(request)

        try:
            # 判断认证类型
            if authorization.startswith("Bearer "):
                # User JWT认证
                await self._authenticate_user(request, authorization[7:])
            elif authorization.startswith("ApiKey "):
                # Agent API Key认证
                await self._authenticate_agent(request, authorization[7:])
            else:
                # 不支持的认证类型
                return self._unauthorized_response("Unsupported authentication type")

        except JWTExpiredError:
            return self._unauthorized_response("Token has expired")
        except JWTInvalidError:
            return self._unauthorized_response("Invalid token")
        except ValueError as e:
            return self._unauthorized_response(str(e))

        # 继续处理请求
        return await call_next(request)

    async def _authenticate_user(self, request: Request, token: str) -> None:
        """User JWT认证。

        Args:
            request: 请求对象
            token: JWT token

        Raises:
            JWTExpiredError: Token已过期
            JWTInvalidError: Token无效
        """
        # 验证token并提取用户ID
        user_id = jwt_service.get_user_id_from_token(token)

        # 注入Actor和user_id
        request.state.actor = Actor.from_user(user_id)
        request.state.user_id = user_id
        request.state.authenticated = True
        request.state.auth_type = "user"

    async def _authenticate_agent(self, request: Request, api_key_str: str) -> None:
        """Agent API Key认证。

        Args:
            request: 请求对象
            api_key_str: API Key字符串

        Raises:
            ValueError: API Key无效
        """
        # 创建ApiKey值对象
        try:
            api_key = ApiKey(api_key_str)
        except ValueError as e:
            raise ValueError(f"Invalid API Key format: {e}")

        # 获取数据库会话
        async for session in get_db_session():
            agent_repo = PostgresAgentRepository(session)

            # 使用前缀快速查找Agent
            prefix = api_key.get_prefix()
            agent = await agent_repo.find_by_api_key_prefix(prefix)

            if not agent:
                raise ValueError("Invalid API Key")

            # 验证完整的API Key
            if not agent.verify_api_key(api_key):
                raise ValueError("Invalid API Key")

            # 检查Agent是否激活
            if not agent.is_active:
                raise ValueError("Agent is not active")

            # 注入Actor
            request.state.actor = Actor.from_agent(agent.id)
            request.state.agent_id = agent.id
            request.state.authenticated = True
            request.state.auth_type = "agent"

            break

    def _is_excluded_path(self, path: str) -> bool:
        """检查路径是否在排除列表中。

        Args:
            path: 请求路径

        Returns:
            是否排除
        """
        # 精确匹配
        if path in self.EXCLUDED_PATHS:
            return True

        # 前缀匹配
        for excluded_path in self.EXCLUDED_PATHS:
            if path.startswith(excluded_path):
                return True

        return False

    def _unauthorized_response(self, message: str) -> Response:
        """返回401未授权响应。

        Args:
            message: 错误消息

        Returns:
            Response对象
        """
        return Response(
            content=ApiResponse(
                code=401,
                status=401,
                message=message,
                data=None,
            ).model_dump_json(),
            status_code=401,
            media_type="application/json",
        )
