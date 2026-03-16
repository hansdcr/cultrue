"""Agent API schemas."""
from typing import Optional
from pydantic import BaseModel, Field


class ActorSchema(BaseModel):
    """Actor Schema."""
    actor_type: str = Field(..., description="Actor类型: 'user' or 'agent'")
    actor_id: str = Field(..., description="Actor ID")


class AgentConfigSchema(BaseModel):
    """Agent配置Schema."""
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2000, gt=0)
    model: str = Field(default="claude-sonnet-4")
    top_p: Optional[float] = Field(default=None, ge=0, le=1)
    frequency_penalty: Optional[float] = Field(default=None)
    presence_penalty: Optional[float] = Field(default=None)


class RegisterAgentRequest(BaseModel):
    """Agent注册请求."""
    agent_id: str = Field(..., description="Agent ID，格式: agent_xxx")
    name: str = Field(..., min_length=1, max_length=100)
    avatar: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None)
    system_prompt: Optional[str] = Field(default=None)
    model_config: Optional[AgentConfigSchema] = None


class RegisterAgentResponse(BaseModel):
    """Agent注册响应."""
    agent: dict
    api_key: str = Field(..., description="API Key（仅此一次返回）")


class CreateAgentRequest(BaseModel):
    """创建Agent请求（管理员）."""
    agent_id: str = Field(..., description="Agent ID，格式: agent_xxx")
    name: str = Field(..., min_length=1, max_length=100)
    avatar: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None)
    system_prompt: Optional[str] = Field(default=None)
    model_config: Optional[AgentConfigSchema] = None


class UpdateAgentRequest(BaseModel):
    """更新Agent请求."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    avatar: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_config: Optional[AgentConfigSchema] = None


class AgentResponse(BaseModel):
    """Agent响应."""
    id: str
    agent_id: str
    name: str
    avatar: Optional[str]
    description: Optional[str]
    system_prompt: Optional[str]
    model_config: dict
    api_key_prefix: str
    is_active: bool
    created_by: Optional[str]
    created_at: str
    updated_at: str


class ListAgentsResponse(BaseModel):
    """Agent列表响应."""
    items: list[AgentResponse]
    total: int
    limit: int
    offset: int


class RegenerateApiKeyResponse(BaseModel):
    """重新生成API Key响应."""
    api_key: str = Field(..., description="新的API Key（仅此一次返回）")
