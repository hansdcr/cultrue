"""Conversation相关的Pydantic schemas."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ActorSchema(BaseModel):
    """Actor schema."""
    actor_type: str = Field(..., description="Actor类型: user或agent")
    actor_id: str = Field(..., description="Actor ID")


class CreateConversationRequest(BaseModel):
    """创建会话请求。"""
    conversation_type: str = Field(..., description="会话类型: direct或group")
    members: List[ActorSchema] = Field(..., description="成员列表")
    title: Optional[str] = Field(None, max_length=200, description="会话标题(群聊必填)")


class AddMemberRequest(BaseModel):
    """添加成员请求。"""
    actor_type: str = Field(..., description="Actor类型: user或agent")
    actor_id: str = Field(..., description="Actor ID")


class RemoveMemberRequest(BaseModel):
    """移除成员请求。"""
    actor_type: str = Field(..., description="Actor类型: user或agent")
    actor_id: str = Field(..., description="Actor ID")


class ConversationResponse(BaseModel):
    """会话响应。"""
    id: str = Field(..., description="会话ID")
    conversation_type: str = Field(..., description="会话类型")
    status: str = Field(..., description="会话状态")
    members: List[ActorSchema] = Field(..., description="成员列表")
    message_count: int = Field(..., description="消息数量")
    title: Optional[str] = Field(None, description="会话标题")
    last_message_at: Optional[datetime] = Field(None, description="最后消息时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    """会话列表响应。"""
    items: List[ConversationResponse] = Field(..., description="会话列表")
    total: int = Field(..., description="总数")
    limit: int = Field(..., description="每页数量")
    offset: int = Field(..., description="偏移量")
