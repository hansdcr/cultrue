"""认证中间件。

验证JWT Token并将用户信息注入到请求中。
"""

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.security.jwt_service import (
    JWTExpiredError,
    JWTInvalidError,
    jwt_service,
)
from src.interfaces.api.schemas.response import ApiResponse


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件。

    从请求头中提取JWT Token，验证后将用户ID注入到request.state中。
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

        # 提取token
        token = self._extract_token(request)
        print(f"[AuthMiddleware] Path: {request.url.path}")
        print(f"[AuthMiddleware] Token: {token[:20] if token else None}")

        if not token:
            # 如果没有token，继续处理请求（由路由的依赖来决定是否需要认证）
            return await call_next(request)

        try:
            # 验证token并提取用户ID
            user_id = jwt_service.get_user_id_from_token(token)

            # 将用户ID注入到request.state中
            request.state.user_id = user_id
            request.state.authenticated = True

        except JWTExpiredError:
            # Token已过期
            return Response(
                content=ApiResponse(
                    code=401,
                    status=401,
                    message="Token has expired",
                    data=None,
                ).model_dump_json(),
                status_code=401,
                media_type="application/json",
            )

        except JWTInvalidError:
            # Token无效
            return Response(
                content=ApiResponse(
                    code=401,
                    status=401,
                    message="Invalid token",
                    data=None,
                ).model_dump_json(),
                status_code=401,
                media_type="application/json",
            )

        # 继续处理请求
        return await call_next(request)

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

    def _extract_token(self, request: Request) -> str | None:
        """从请求头中提取JWT Token。

        Args:
            request: 请求对象

        Returns:
            JWT Token字符串，如果不存在则返回None
        """
        authorization = request.headers.get("Authorization")

        if not authorization:
            return None

        # 检查是否是Bearer token
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]
