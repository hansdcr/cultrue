"""Agent ID value object."""
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentId:
    """Agent ID值对象。

    格式: agent_hans, agent_alice, agent_bob
    """
    value: str

    def __post_init__(self):
        """验证Agent ID格式。"""
        if not self.value.startswith('agent_'):
            raise ValueError("Agent ID must start with 'agent_'")
        if len(self.value) <= 6:  # "agent_" is 6 characters
            raise ValueError("Agent ID must have a name after 'agent_'")

    def __str__(self) -> str:
        """返回字符串表示。"""
        return self.value
