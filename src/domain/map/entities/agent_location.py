"""Agent地理位置实体。"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from math import radians, sin, cos, sqrt, atan2


@dataclass
class AgentLocation:
    """Agent地理位置实体。

    表示一个Agent在地图上的位置。一个Agent可以有多个位置。
    """
    id: UUID
    agent_id: UUID  # 关联的Agent ID
    latitude: float  # 纬度
    longitude: float  # 经度
    address: str
    is_active: bool  # 是否在地图上显示
    display_order: int  # 显示优先级（用于同一Agent多个位置时的排序）
    metadata: Optional[dict]  # 扩展信息（如：营业时间、标签等）
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        agent_id: UUID,
        latitude: float,
        longitude: float,
        address: str,
        is_active: bool = True,
        display_order: int = 0,
        metadata: Optional[dict] = None
    ) -> "AgentLocation":
        """创建Agent地理位置。

        Args:
            agent_id: Agent ID
            latitude: 纬度（-90到90）
            longitude: 经度（-180到180）
            address: 地址
            is_active: 是否激活
            display_order: 显示优先级
            metadata: 扩展信息

        Returns:
            AgentLocation实例

        Raises:
            ValueError: 经纬度不合法
        """
