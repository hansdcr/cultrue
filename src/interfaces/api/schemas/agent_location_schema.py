"""Agent地理位置API Schema。"""
from typing import Optional
from pydantic import BaseModel, Field


class CreateAgentLocationRequest(BaseModel):
    """创建Agent位置请求。"""
    agent_id: str = Field(..., description="Agent ID")
    latitude: float = Field(..., ge=-90, le=90, description="纬度")
    longitude: float = Field(..., ge=-180, le=180, description="经度")
    address: str = Field(..., max_length=500, description="地址")
    is_active: bool = Field(default=True, description="是否激活")
    display_order: int = Field(default=0, description="显示优先级")
    metadata: Optional[dict] = Field(default=None, description="扩展信息")


class AgentInfoSchema(BaseModel):
    """Agent信息Schema（嵌套在响应中）。"""
    id: str
    agent_id: str
    name: str
    avatar: Optional[str]
    description: Optional[str]


class AgentLocationResponse(BaseModel):
    """Agent位置响应。"""
    location_id: str
    agent: AgentInfoSchema
    latitude: float
    longitude: float
    address: str
    is_active: bool
    display_order: int
    distance: Optional[float] = None  # 距离（米），仅在nearby查询时返回
    created_at: str
    updated_at: str


class NearbyAgentsResponse(BaseModel):
    """周边Agent响应。"""
    items: list[AgentLocationResponse]
    total: int
    center: dict  # {"latitude": float, "longitude": float}
    radius: int


class AgentLocationsResponse(BaseModel):
    """Agent位置列表响应。"""
    items: list[AgentLocationResponse]
    total: int
