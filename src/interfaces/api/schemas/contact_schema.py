"""Contact API schemas."""
from typing import Optional
from pydantic import BaseModel, Field


class AddContactRequest(BaseModel):
    """添加联系人请求."""
    target_type: str = Field(..., description="目标类型: 'user' or 'agent'")
    target_id: str = Field(..., description="目标ID")
    contact_type: str = Field(default="friend", description="联系人类型: friend, favorite, colleague, blocked")
    alias: Optional[str] = Field(default=None, max_length=100)


class UpdateContactRequest(BaseModel):
    """更新联系人请求."""
    alias: Optional[str] = Field(default=None, max_length=100)
    is_favorite: Optional[bool] = None


class ActorInfoSchema(BaseModel):
    """Actor信息Schema."""
    actor_type: str
    actor_id: str


class ContactResponse(BaseModel):
    """Contact响应."""
    id: str
    owner: ActorInfoSchema
    target: ActorInfoSchema
    contact_type: str
    alias: Optional[str]
    is_favorite: bool
    last_interaction_at: Optional[str]
    created_at: str


class ListContactsResponse(BaseModel):
    """联系人列表响应."""
    items: list[ContactResponse]
    total: int
    limit: int
    offset: int
