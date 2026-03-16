"""Agent configuration value object."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentConfig:
    """Agent配置值对象。

    包含Agent的模型配置参数。
    """
    temperature: float = 0.7
    max_tokens: int = 2000
    model: str = "claude-sonnet-4"
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None

    def __post_init__(self):
        """验证配置参数。"""
        if not 0 <= self.temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if self.top_p is not None and not 0 <= self.top_p <= 1:
            raise ValueError("top_p must be between 0 and 1")

    def to_dict(self) -> dict:
        """转换为字典。

        Returns:
            配置字典
        """
        result = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "model": self.model,
        }
        if self.top_p is not None:
            result["top_p"] = self.top_p
        if self.frequency_penalty is not None:
            result["frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty is not None:
            result["presence_penalty"] = self.presence_penalty
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "AgentConfig":
        """从字典创建配置。

        Args:
            data: 配置字典

        Returns:
            AgentConfig实例
        """
        return cls(
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 2000),
            model=data.get("model", "claude-sonnet-4"),
            top_p=data.get("top_p"),
            frequency_penalty=data.get("frequency_penalty"),
            presence_penalty=data.get("presence_penalty"),
        )
