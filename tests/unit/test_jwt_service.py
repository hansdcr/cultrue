"""JWT Token服务单元测试。"""

import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from src.infrastructure.security.jwt_service import (
    JWTExpiredError,
    JWTInvalidError,
    JWTInvalidTypeError,
    JWTService,
    jwt_service,
)


class TestJWTService:
    """测试JWTService类。"""

    def test_create_access_token(self):
        """测试创建访问令牌。"""
        service = JWTService()
        user_id = "test_user_123"

        token = service.create_access_token(user_id)

        # 验证token不为空
        assert token
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """测试创建刷新令牌。"""
        service = JWTService()
        user_id = "test_user_456"

        token = service.create_refresh_token(user_id)

        # 验证token不为空
        assert token
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token(self):
        """测试解码令牌。"""
        service = JWTService()
        user_id = "test_user_789"

        token = service.create_access_token(user_id)
        payload = service.decode_token(token)

        # 验证payload包含正确的信息
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_verify_access_token(self):
        """测试验证访问令牌。"""
        service = JWTService()
        user_id = "test_user_verify"

        token = service.create_access_token(user_id)
        result = service.verify_token(token, token_type="access")

        assert result is True

    def test_verify_refresh_token(self):
        """测试验证刷新令牌。"""
        service = JWTService()
        user_id = "test_user_refresh"

        token = service.create_refresh_token(user_id)
        result = service.verify_token(token, token_type="refresh")

        assert result is True

    def test_verify_token_type_mismatch(self):
        """测试验证令牌类型不匹配。"""
        service = JWTService()
        user_id = "test_user_mismatch"

        # 创建访问令牌但尝试作为刷新令牌验证
        token = service.create_access_token(user_id)

        with pytest.raises(JWTInvalidTypeError) as exc_info:
            service.verify_token(token, token_type="refresh")

        assert "Expected token type 'refresh'" in str(exc_info.value)

    def test_decode_invalid_token(self):
        """测试解码无效令牌。"""
        service = JWTService()
        invalid_token = "invalid.token.string"

        with pytest.raises(JWTInvalidError) as exc_info:
            service.decode_token(invalid_token)

        assert "Invalid token" in str(exc_info.value)

    def test_decode_expired_token(self):
        """测试解码过期令牌。"""
        service = JWTService()
        user_id = "test_user_expired"

        # 创建一个已经过期的令牌
        now = datetime.now(timezone.utc)
        expire = now - timedelta(seconds=1)  # 1秒前过期

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now - timedelta(seconds=2),
            "type": "access",
        }

        expired_token = jwt.encode(
            payload, service._secret_key, algorithm=service._algorithm
        )

        with pytest.raises(JWTExpiredError) as exc_info:
            service.decode_token(expired_token)

        assert "Token has expired" in str(exc_info.value)

    def test_get_user_id_from_token(self):
        """测试从令牌中获取用户ID。"""
        service = JWTService()
        user_id = "test_user_get_id"

        token = service.create_access_token(user_id)
        extracted_user_id = service.get_user_id_from_token(token)

        assert extracted_user_id == user_id

    def test_get_user_id_from_invalid_token(self):
        """测试从无效令牌中获取用户ID。"""
        service = JWTService()
        invalid_token = "invalid.token.string"

        with pytest.raises(JWTInvalidError):
            service.get_user_id_from_token(invalid_token)

    def test_access_token_expiration_time(self):
        """测试访问令牌的过期时间设置正确。"""
        service = JWTService()
        user_id = "test_user_exp_time"

        token = service.create_access_token(user_id)
        payload = service.decode_token(token)

        # 计算过期时间差
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        time_diff = exp_time - iat_time

        # 验证过期时间约为15分钟（允许1秒误差）
        expected_minutes = service._access_token_expire_minutes
        assert abs(time_diff.total_seconds() - expected_minutes * 60) < 1

    def test_refresh_token_expiration_time(self):
        """测试刷新令牌的过期时间设置正确。"""
        service = JWTService()
        user_id = "test_user_refresh_exp"

        token = service.create_refresh_token(user_id)
        payload = service.decode_token(token)

        # 计算过期时间差
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        time_diff = exp_time - iat_time

        # 验证过期时间约为7天（允许1秒误差）
        expected_days = service._refresh_token_expire_days
        assert abs(time_diff.total_seconds() - expected_days * 86400) < 1

    def test_global_instance(self):
        """测试全局实例可用。"""
        user_id = "test_global_jwt"

        token = jwt_service.create_access_token(user_id)
        extracted_user_id = jwt_service.get_user_id_from_token(token)

        assert extracted_user_id == user_id
