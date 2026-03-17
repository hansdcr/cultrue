"""Agent地理位置实体。"""
from dataclasses import dataclass
from datetime import datetime
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
        # 验证经纬度合法性
        if not (-90 <= latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180")

        return cls(
            id=uuid4(),
            agent_id=agent_id,
            latitude=latitude,
            longitude=longitude,
            address=address,
            is_active=is_active,
            display_order=display_order,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    def distance_to(self, latitude: float, longitude: float) -> float:
        """计算到指定坐标的距离（米）。

        使用Haversine公式计算两点间的距离。

        Args:
            latitude: 目标纬度
            longitude: 目标经度

        Returns:
            距离（米）
        """
        R = 6371000  # 地球半径（米）
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(latitude), radians(longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    def activate(self) -> None:
        """激活位置（在地图上显示）。"""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """停用位置（在地图上隐藏）。"""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def update_location(
        self,
        latitude: float,
        longitude: float,
        address: str
    ) -> None:
        """更新位置信息。

        Args:
            latitude: 新纬度
            longitude: 新经度
            address: 新地址

        Raises:
            ValueError: 经纬度不合法
        """
        if not (-90 <= latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180")

        self.latitude = latitude
        self.longitude = longitude
        self.address = address
        self.updated_at = datetime.utcnow()
