"""Message相关的Pydantic schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.interfaces.api.schemas.conversation_schema import ActorSchema


class SendMessageRequest(BaseModel):
    """发送消息请求。"""
    message_type: str = Field(default="text", description="消息类型")
    content: str = Field(..., min_length=1, description="消息内容")
    metadata: Optional[dict] = Field(None, description="元数据")


class MessageResponse(BaseModel):
    """消息响应。"""
    id: str = Field(..., description="消息ID")
    conversation_id: str = Field(..., description="会话ID")
    sender: ActorSchema = Field(..., description="发送者")
    message_type: str = Field(..., description="消息类型")
    content: str = Field(..., description="消息内容")
    metadata: Optional[dict] = Field(None, description="元数据")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseModel):
    """消息列表响应。"""
    items: List[MessageResponse] = Field(..., description="消息列表")
    total: int = Field(..., description="总数")
    limit: int = Field(..., description="每页数量")
    offset: int = Field(..., description="偏移量")
