"""JWT Token服务。

提供JWT Token的生成、验证和解码功能。
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError

from src.infrastructure.config import settings


class JWTTokenError(Exception):
    """JWT Token基础异常。"""

    pass


class JWTExpiredError(JWTTokenError):
    """JWT Token已过期异常。"""

    pass


class JWTInvalidError(JWTTokenError):
    """JWT Token无效异常。"""

    pass


class JWTInvalidTypeError(JWTTokenError):
    """JWT Token类型不匹配异常。"""

    pass


class JWTService:
    """JWT Token服务。

    提供JWT Token的生成、验证和解码功能。
    """

    def __init__(self) -> None:
        """初始化JWT服务。"""
        self._secret_key = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self._refresh_token_expire_days = settings.jwt_refresh_token_expire_days

    def create_access_token(self, user_id: str) -> str:
        """创建访问令牌。

        Args:
            user_id: 用户ID

        Returns:
            JWT访问令牌字符串
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self._access_token_expire_minutes)

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "type": "access",
        }

        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        return token

    def create_refresh_token(self, user_id: str) -> str:
        """创建刷新令牌。

        Args:
            user_id: 用户ID

        Returns:
            JWT刷新令牌字符串
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self._refresh_token_expire_days)

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "type": "refresh",
        }

        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        return token

    def decode_token(self, token: str) -> dict[str, Any]:
        """解码JWT令牌。

        Args:
            token: JWT令牌字符串

        Returns:
            解码后的payload字典

        Raises:
            JWTExpiredError: 令牌已过期
            JWTInvalidError: 令牌无效
        """
        try:
            payload = jwt.decode(
                token, self._secret_key, algorithms=[self._algorithm]
            )
            return payload
        except ExpiredSignatureError as e:
            raise JWTExpiredError("Token has expired") from e
        except (DecodeError, InvalidTokenError) as e:
            raise JWTInvalidError("Invalid token") from e

    def verify_token(self, token: str, token_type: str = "access") -> bool:
        """验证JWT令牌。

        Args:
            token: JWT令牌字符串
            token_type: 令牌类型（"access" 或 "refresh"）

        Returns:
            令牌是否有效

        Raises:
            JWTExpiredError: 令牌已过期
            JWTInvalidError: 令牌无效
            JWTInvalidTypeError: 令牌类型不匹配
        """
        payload = self.decode_token(token)

        # 验证令牌类型
        if payload.get("type") != token_type:
            raise JWTInvalidTypeError(
                f"Expected token type '{token_type}', got '{payload.get('type')}'"
            )

        return True

    def get_user_id_from_token(self, token: str) -> str:
        """从JWT令牌中获取用户ID。

        Args:
            token: JWT令牌字符串

        Returns:
            用户ID

        Raises:
            JWTExpiredError: 令牌已过期
            JWTInvalidError: 令牌无效或缺少用户ID
        """
        payload = self.decode_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise JWTInvalidError("Token does not contain user ID")

        return user_id


# 创建全局实例
jwt_service = JWTService()
