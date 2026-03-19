from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class UpdateUserRequest(BaseModel):
    """更新用户请求。"""

    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")


class UserResponse(BaseModel):
    """用户响应。"""

    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, description="全名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")
    wallet_balance: Decimal = Field(..., description="钱包余额")
    is_active: bool = Field(..., description="是否激活")
    is_verified: bool = Field(..., description="是否已验证")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")

    class Config:
        from_attributes = True


class SearchResultItem(BaseModel):
    """统一搜索结果条目（user 或 agent）。"""

    actor_type: str = Field(..., description="类型: 'user' | 'agent'")
    actor_id: str = Field(..., description="UUID")
    name: str = Field(..., description="显示名称")
    avatar: Optional[str] = Field(None, description="头像")
    description: Optional[str] = Field(None, description="简介/邮箱")
    agent_id: Optional[str] = Field(None, description="agent 字符串 ID，仅 agent 类型有值")
