"""认证相关的Pydantic schemas。

定义认证API的请求和响应模型。
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """注册请求。"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")


class LoginRequest(BaseModel):
    """登录请求。"""

    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码")


class RefreshTokenRequest(BaseModel):
    """刷新Token请求。"""

    refresh_token: str = Field(..., description="刷新令牌")


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


class TokenResponse(BaseModel):
    """Token响应。"""

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class LoginResponse(BaseModel):
    """登录响应。"""

    user: UserResponse = Field(..., description="用户信息")
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class AgentLoginRequest(BaseModel):
    """Agent登录请求。"""

    agent_id: str = Field(..., description="Agent ID（如 agent_libai）")
    api_key: str = Field(..., description="API Key")


class AgentResponse(BaseModel):
    """Agent响应（登录用）。"""

    id: str = Field(..., description="Agent UUID")
    agent_id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent名称")
    avatar: Optional[str] = Field(None, description="头像")
    description: Optional[str] = Field(None, description="描述")
    is_active: bool = Field(..., description="是否激活")

    class Config:
        from_attributes = True


class AgentLoginResponse(BaseModel):
    """Agent登录响应。"""

    agent: AgentResponse = Field(..., description="Agent信息")
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
