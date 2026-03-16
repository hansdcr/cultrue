"""API Key value object."""
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class ApiKey:
    """Agent API Key值对象。

    格式: ak_<32-char-random-string>
    用于Agent的独立认证。
    """
    value: str

    def __post_init__(self):
        """验证API Key格式。"""
        if not self.value.startswith('ak_'):
            raise ValueError("API Key must start with 'ak_'")
        if len(self.value) < 10:  # ak_ + at least some characters
            raise ValueError("API Key is too short")

    @classmethod
    def generate(cls) -> "ApiKey":
        """生成新的API Key。

        Returns:
            新生成的ApiKey实例
        """
        random_str = secrets.token_urlsafe(24)[:32]
        return cls(f"ak_{random_str}")

    def get_prefix(self) -> str:
        """获取前缀（前16个字符，用于索引）。

        Returns:
            API Key前缀
        """
        return self.value[:16]  # "ak_" + 前12个字符

    def mask(self) -> str:
        """返回掩码版本（用于显示）。

        Returns:
            掩码后的API Key
        """
        if len(self.value) <= 14:
            return f"{self.value[:6]}...{self.value[-4:]}"
        return f"{self.value[:10]}...{self.value[-4:]}"

    def __str__(self) -> str:
        """返回掩码版本，避免泄露完整Key。"""
        return self.mask()
