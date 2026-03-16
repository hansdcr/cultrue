"""密码加密服务单元测试。"""

import pytest

from src.infrastructure.security.password_hasher import PasswordHasher, password_hasher


class TestPasswordHasher:
    """测试PasswordHasher类。"""

    def test_hash_password(self):
        """测试密码加密功能。"""
        hasher = PasswordHasher()
        password = "test_password_123"

        hashed = hasher.hash_password(password)

        # 验证加密后的密码不等于原始密码
        assert hashed != password
        # 验证加密后的密码不为空
        assert len(hashed) > 0
        # 验证加密后的密码以$2b$开头（bcrypt特征）
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """测试验证正确的密码。"""
        hasher = PasswordHasher()
        password = "correct_password"
        hashed = hasher.hash_password(password)

        # 验证正确的密码
        result = hasher.verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self):
        """测试验证错误的密码。"""
        hasher = PasswordHasher()
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hasher.hash_password(password)

        # 验证错误的密码
        result = hasher.verify_password(wrong_password, hashed)
        assert result is False

    def test_hash_same_password_twice_different_hashes(self):
        """测试相同密码两次加密产生不同的哈希值（因为salt不同）。"""
        hasher = PasswordHasher()
        password = "same_password"

        hash1 = hasher.hash_password(password)
        hash2 = hasher.hash_password(password)

        # 两次加密的结果应该不同（因为salt不同）
        assert hash1 != hash2
        # 但都应该能验证原始密码
        assert hasher.verify_password(password, hash1)
        assert hasher.verify_password(password, hash2)

    def test_global_instance(self):
        """测试全局实例可用。"""
        password = "test_global"
        hashed = password_hasher.hash_password(password)

        assert password_hasher.verify_password(password, hashed)
