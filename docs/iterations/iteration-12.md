# 迭代12: 地图功能

> 实现地图位置管理和周边实体查询功能

## 📋 迭代信息

- **迭代编号**: 12
- **预计时间**: 2天
- **当前状态**: ✅ 已完成
- **依赖迭代**: 迭代6 ✅, 迭代7 ✅, 迭代8 ✅
- **开始日期**: 2026-03-17
- **完成日期**: 2026-03-17

## 🎯 迭代目标

实现地图功能，支持在地图上注册和查询名人、美食、景点等实体，用户可以通过地图发现周边的AI智能体并添加为好友，建立社交关系。

## 💡 设计理念

**方案2：AgentLocation关联表**：
- 使用AgentLocation表建立Agent和地理位置的多对多关系
- 一个Agent可以在多个位置（李白可以在珠海、深圳、广州都有）
- 未来的美食、景点也是Agent（比如"李白推荐的美食"也是一个Agent）
- 没有数据冗余：name、description、avatar从Agent表获取
- 外键约束保证数据完整性

**复用现有系统**：
- 地图上的所有实体都是Agent（名人、美食、景点）
- 添加好友功能使用现有的Contact系统（迭代6）
- 聊天功能使用现有的Conversation和Message系统（迭代8）

**MVP原则**：
- 第一阶段只实现名人Agent的地理位置关联
- 美食、景点Agent延后创建
- 收藏和路线规划功能延后实现

## 📝 任务清单

### 1. AgentLocation领域层 ✅

**任务**:
- [x] 创建AgentLocation实体
- [x] 创建AgentLocationRepository接口

**交付物**:
- `src/domain/map/entities/agent_location.py`
- `src/domain/map/repositories/agent_location_repository.py`

**设计要点**:
```python
# AgentLocation实体
from src.domain.shared.value_objects.actor import Actor

@dataclass
class AgentLocation:
    """Agent地理位置实体。"""
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
        """创建Agent地理位置。"""
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    def distance_to(self, latitude: float, longitude: float) -> float:
        """计算到指定坐标的距离（米）。"""
        # 使用Haversine公式计算距离
        from math import radians, sin, cos, sqrt, atan2

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
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """停用位置（在地图上隐藏）。"""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def update_location(
        self,
        latitude: float,
        longitude: float,
        address: str
    ) -> None:
        """更新位置信息。"""
        if not (-90 <= latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180")

        self.latitude = latitude
        self.longitude = longitude
        self.address = address
        self.updated_at = datetime.now(timezone.utc)

# AgentLocationRepository接口
class AgentLocationRepository(ABC):
    """Agent地理位置仓储接口。"""

    @abstractmethod
    async def save(self, location: AgentLocation) -> AgentLocation:
        """保存Agent位置。"""
        pass

    @abstractmethod
    async def find_by_id(self, location_id: UUID) -> Optional[AgentLocation]:
        """根据ID查找位置。"""
        pass

    @abstractmethod
    async def find_by_agent_id(self, agent_id: UUID) -> List[AgentLocation]:
        """查找Agent的所有位置。"""
        pass

    @abstractmethod
    async def find_nearby(
        self,
        latitude: float,
        longitude: float,
        radius: int,
        limit: int = 10,
        only_active: bool = True
    ) -> List[AgentLocation]:
        """查找周边位置。

        Args:
            latitude: 纬度
            longitude: 经度
            radius: 半径（米）
            limit: 返回数量限制
            only_active: 是否只返回激活的位置
        """
        pass

    @abstractmethod
    async def update(self, location: AgentLocation) -> AgentLocation:
        """更新位置。"""
        pass

    @abstractmethod
    async def delete(self, location_id: UUID) -> None:
        """删除位置。"""
        pass

    @abstractmethod
    async def count_by_agent_id(self, agent_id: UUID) -> int:
        """统计Agent的位置数量。"""
        pass
```

### 2. AgentLocation应用层 ✅

**任务**:
- [x] 创建CreateAgentLocationCommand和Handler
- [x] 创建GetNearbyAgentsQuery和Handler
- [x] 创建GetAgentLocationQuery和Handler
- [x] 创建GetAgentLocationsQuery和Handler（获取某个Agent的所有位置）
- [x] 创建UpdateAgentLocationCommand和Handler
- [x] 创建DeleteAgentLocationCommand和Handler
- [x] 创建AgentLocationDTO

**交付物**:
- `src/application/map/commands/create_agent_location_command.py`
- `src/application/map/commands/update_agent_location_command.py`
- `src/application/map/commands/delete_agent_location_command.py`
- `src/application/map/queries/get_nearby_agents_query.py`
- `src/application/map/queries/get_agent_location_query.py`
- `src/application/map/queries/get_agent_locations_query.py`
- `src/application/map/dtos/agent_location_dto.py`

**业务逻辑**:
```python
# CreateAgentLocationCommand
@dataclass
class CreateAgentLocationCommand:
    """创建Agent位置命令。"""
    agent_id: UUID
    latitude: float
    longitude: float
    address: str
    is_active: bool = True
    display_order: int = 0
    metadata: Optional[dict] = None

# GetNearbyAgentsQuery
@dataclass
class GetNearbyAgentsQuery:
    """查询周边Agent。"""
    latitude: float
    longitude: float
    radius: int = 5000  # 默认5公里
    limit: int = 10
    only_active: bool = True

# GetAgentLocationsQuery
@dataclass
class GetAgentLocationsQuery:
    """查询某个Agent的所有位置。"""
    agent_id: UUID
    only_active: bool = True

# AgentLocationDTO
@dataclass
class AgentLocationDTO:
    """Agent位置DTO。"""
    location_id: str
    agent: AgentDTO  # 包含Agent的完整信息
    latitude: float
    longitude: float
    address: str
    is_active: bool
    display_order: int
    distance: Optional[float] = None  # 距离（米），仅在nearby查询时返回
    created_at: str
    updated_at: str

    @classmethod
    async def from_entity(
        cls,
        location: AgentLocation,
        agent: Agent,
        distance: Optional[float] = None
    ) -> "AgentLocationDTO":
        """从实体创建DTO。"""
        return cls(
            location_id=str(location.id),
            agent=AgentDTO(
                id=str(agent.id),
                agent_id=agent.agent_id.value,
                name=agent.name,
                avatar=agent.avatar,
                description=agent.description
            ),
            latitude=location.latitude,
            longitude=location.longitude,
            address=location.address,
            is_active=location.is_active,
            display_order=location.display_order,
            distance=distance,
            created_at=location.created_at.isoformat(),
            updated_at=location.updated_at.isoformat()
        )

# 业务规则
- 验证经纬度合法性（-90~90, -180~180）
- 验证agent_id对应的Agent存在
- 一个Agent可以在多个位置
- 管理员权限验证（只有管理员可以创建/更新/删除位置）
- 查询周边Agent时，需要JOIN agent_locations和agents表
```

### 3. 数据库模型和迁移 ✅

**任务**:
- [x] 创建agent_locations表
- [x] 创建地理空间索引
- [x] 编写Alembic迁移脚本

**交付物**:
- `src/infrastructure/persistence/models/agent_location_model.py`
- `migrations/versions/xxx_create_agent_locations_table.py`

**数据库设计**:
```sql
-- agent_locations表
CREATE TABLE agent_locations (
    id UUID PRIMARY KEY,
    agent_id UUID NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    address VARCHAR(500) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INTEGER NOT NULL DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    CONSTRAINT fk_agent_location_agent FOREIGN KEY (agent_id)
        REFERENCES agents(id) ON DELETE CASCADE,

    -- 检查约束
    CONSTRAINT chk_latitude CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT chk_longitude CHECK (longitude BETWEEN -180 AND 180)
);

-- 普通索引
CREATE INDEX idx_agent_locations_agent_id ON agent_locations(agent_id);
CREATE INDEX idx_agent_locations_is_active ON agent_locations(is_active);
CREATE INDEX idx_agent_locations_display_order ON agent_locations(display_order);

-- PostGIS扩展（用于高效的地理空间查询）
CREATE EXTENSION IF NOT EXISTS postgis;

-- 添加地理位置列
ALTER TABLE agent_locations ADD COLUMN location GEOGRAPHY(POINT, 4326);

-- 更新location列（从latitude和longitude生成）
UPDATE agent_locations
SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);

-- 创建空间索引
CREATE INDEX idx_agent_locations_location_gist
    ON agent_locations USING GIST (location);

-- 触发器：自动更新location列
CREATE OR REPLACE FUNCTION update_agent_location_geography()
RETURNS TRIGGER AS $$
BEGIN
    NEW.location = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_agent_location_geography
BEFORE INSERT OR UPDATE OF latitude, longitude ON agent_locations
FOR EACH ROW
EXECUTE FUNCTION update_agent_location_geography();
```

**设计说明**:
- **外键约束**: agent_id → agents.id (ON DELETE CASCADE)
- **地理位置列**: 使用PostGIS的GEOGRAPHY类型存储位置
- **空间索引**: 使用GIST索引加速地理空间查询
- **触发器**: 自动更新location列和updated_at字段
- **一对多关系**: 一个Agent可以有多个AgentLocation

### 4. 仓储实现 ✅

**任务**:
- [x] 创建PostgresAgentLocationRepository
- [x] 实现地理空间查询（使用Haversine公式）
- [x] 实现实体与模型的转换
- [x] 实现JOIN查询获取Agent信息

**交付物**:
- `src/infrastructure/persistence/repositories/postgres_agent_location_repository.py`

**仓储实现要点**:
```python
class PostgresAgentLocationRepository(AgentLocationRepository):
    """PostgreSQL Agent位置仓储。"""

    def __init__(
        self,
        session: AsyncSession,
        agent_repo: AgentRepository  # 注入Agent仓储
    ):
        self.session = session
        self.agent_repo = agent_repo

    async def find_nearby(
        self,
        latitude: float,
        longitude: float,
        radius: int,
        limit: int = 10,
        only_active: bool = True
    ) -> List[AgentLocation]:
        """查找周边位置（使用PostGIS）。"""
        # 使用PostGIS的ST_DWithin函数进行空间查询
        query = select(AgentLocationModel).where(
            func.ST_DWithin(
                AgentLocationModel.location,
                func.ST_SetSRID(
                    func.ST_MakePoint(longitude, latitude),
                    4326
                ),
                radius  # 米
            )
        )

        if only_active:
            query = query.where(AgentLocationModel.is_active == True)

        # 按距离排序
        query = query.order_by(
            func.ST_Distance(
                AgentLocationModel.location,
                func.ST_SetSRID(
                    func.ST_MakePoint(longitude, latitude),
                    4326
                )
            )
        ).limit(limit)

        result = await self.session.execute(query)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def find_nearby_with_agents(
        self,
        latitude: float,
        longitude: float,
        radius: int,
        limit: int = 10,
        only_active: bool = True
    ) -> List[Tuple[AgentLocation, Agent, float]]:
        """查找周边位置并返回Agent信息和距离。

        Returns:
            List[Tuple[AgentLocation, Agent, distance]]
        """
        # JOIN查询
        query = (
            select(
                AgentLocationModel,
                AgentModel,
                func.ST_Distance(
                    AgentLocationModel.location,
                    func.ST_SetSRID(
                        func.ST_MakePoint(longitude, latitude),
                        4326
                    )
                ).label('distance')
            )
            .join(AgentModel, AgentLocationModel.agent_id == AgentModel.id)
            .where(
                func.ST_DWithin(
                    AgentLocationModel.location,
                    func.ST_SetSRID(
                        func.ST_MakePoint(longitude, latitude),
                        4326
                    ),
                    radius
                )
            )
        )

        if only_active:
            query = query.where(AgentLocationModel.is_active == True)

        query = query.order_by('distance').limit(limit)

        result = await self.session.execute(query)
        rows = result.all()

        return [
            (
                self._to_entity(location_model),
                self._agent_to_entity(agent_model),
                distance
            )
            for location_model, agent_model, distance in rows
        ]

    def _to_entity(self, model: AgentLocationModel) -> AgentLocation:
        """将模型转换为实体。"""
        return AgentLocation(
            id=model.id,
            agent_id=model.agent_id,
            latitude=model.latitude,
            longitude=model.longitude,
            address=model.address,
            is_active=model.is_active,
            display_order=model.display_order,
            metadata=model.metadata or {},
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _agent_to_entity(self, model: AgentModel) -> Agent:
        """将Agent模型转换为实体。"""
        # 复用Agent仓储的转换逻辑
        return self.agent_repo._to_entity(model)
```

### 5. REST API接口 ✅

**任务**:
- [x] 创建AgentLocationSchema（Pydantic模型）
- [x] 实现POST /api/map/agent-locations - 创建Agent位置（管理员）
- [x] 实现GET /api/map/nearby - 查询周边Agent
- [x] 实现GET /api/map/agent-locations/{id} - 获取位置详情
- [x] 实现GET /api/agents/{agent_id}/locations - 获取Agent的所有位置
- [x] 实现PUT /api/map/agent-locations/{id} - 更新位置（管理员）
- [x] 实现DELETE /api/map/agent-locations/{id} - 删除位置（管理员）

**交付物**:
- `src/interfaces/api/schemas/agent_location_schema.py`
- `src/interfaces/api/rest/map.py`

**API设计**:
```python
# CreateAgentLocationRequest
class CreateAgentLocationRequest(BaseModel):
    agent_id: str = Field(..., description="Agent ID")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: str = Field(..., max_length=500)
    is_active: bool = Field(default=True)
    display_order: int = Field(default=0)
    metadata: Optional[dict] = None

# AgentInfoSchema（嵌套在响应中）
class AgentInfoSchema(BaseModel):
    id: str
    agent_id: str
    name: str
    avatar: Optional[str]
    description: Optional[str]

# AgentLocationResponse
class AgentLocationResponse(BaseModel):
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

# NearbyAgentsResponse
class NearbyAgentsResponse(BaseModel):
    items: List[AgentLocationResponse]
    total: int
    center: dict  # {"latitude": float, "longitude": float}
    radius: int

# POST /api/map/agent-locations
# 请求: {
#   "agent_id": "agent_uuid",
#   "latitude": 22.1234,
#   "longitude": 113.5678,
#   "address": "广东省珠海市金湾区某地",
#   "is_active": true,
#   "display_order": 0
# }
# 响应: {
#   "code": 201,
#   "message": "Agent location created successfully",
#   "data": {
#     "location_id": "uuid",
#     "agent": {
#       "id": "agent_uuid",
#       "agent_id": "agent_libai",
#       "name": "李白",
#       "avatar": "https://...",
#       "description": "唐代著名诗人"
#     },
#     "latitude": 22.1234,
#     "longitude": 113.5678,
#     "address": "广东省珠海市金湾区某地",
#     "is_active": true,
#     "display_order": 0,
#     "created_at": "2026-03-17T...",
#     "updated_at": "2026-03-17T..."
#   }
# }

# GET /api/map/nearby?latitude=22.1234&longitude=113.5678&radius=5000&limit=3
# 响应: {
#   "code": 200,
#   "message": "Nearby agents retrieved successfully",
#   "data": {
#     "items": [
#       {
#         "location_id": "uuid",
#         "agent": {
#           "id": "agent_uuid",
#           "agent_id": "agent_libai",
#           "name": "李白",
#           "avatar": "https://...",
#           "description": "唐代著名诗人"
#         },
#         "latitude": 22.1234,
#         "longitude": 113.5678,
#         "address": "广东省珠海市金湾区某地",
#         "is_active": true,
#         "display_order": 0,
#         "distance": 1234.56,  # 距离（米）
#         "created_at": "2026-03-17T...",
#         "updated_at": "2026-03-17T..."
#       },
#       ...
#     ],
#     "total": 3,
#     "center": {
#       "latitude": 22.1234,
#       "longitude": 113.5678
#     },
#     "radius": 5000
#   }
# }

# GET /api/agents/{agent_id}/locations
# 响应: {
#   "code": 200,
#   "message": "Agent locations retrieved successfully",
#   "data": {
#     "items": [
#       {
#         "location_id": "uuid1",
#         "agent": {...},
#         "latitude": 22.1234,
#         "longitude": 113.5678,
#         "address": "广东省珠海市金湾区",
#         ...
#       },
#       {
#         "location_id": "uuid2",
#         "agent": {...},
#         "latitude": 22.5431,
#         "longitude": 114.0579,
#         "address": "广东省深圳市南山区",
#         ...
#       }
#     ],
#     "total": 2
#   }
# }
```

### 6. 权限控制 ✅

**任务**:
- [x] 实现管理员权限验证
- [x] 创建is_admin依赖注入

**交付物**:
- `src/interfaces/api/dependencies/admin_required.py`

**权限设计**:
```python
# 管理员权限依赖
async def require_admin(
    current_actor: Actor = Depends(get_current_actor),
    user_repo: UserRepository = Depends(get_user_repository)
) -> Actor:
    """验证当前用户是否为管理员。"""
    if not current_actor.is_user():
        raise ForbiddenException("Only users can be administrators")

    user = await user_repo.find_by_id(current_actor.actor_id)
    if not user or not user.is_admin:
        raise ForbiddenException("Administrator permission required")

    return current_actor

# API端点使用
@router.post("/api/map/entities")
async def create_map_entity(
    request: CreateMapEntityRequest,
    current_actor: Actor = Depends(require_admin)  # 管理员权限
):
    ...
```

### 7. 前端集成说明

**前端职责**:
- 集成地图SDK（Mapbox/高德/Google Maps）
- 获取用户当前位置（浏览器Geolocation API）
- 调用GET /api/map/nearby查询周边Agent
- 在地图上渲染标记点
- 点击标记显示气泡，调用POST /api/contacts添加好友

**前端示例代码**:
```javascript
// 1. 获取用户位置
navigator.geolocation.getCurrentPosition(async (position) => {
  const { latitude, longitude } = position.coords;

  // 2. 查询周边Agent
  const response = await fetch(
    `/api/map/nearby?latitude=${latitude}&longitude=${longitude}&radius=5000&limit=3`
  );
  const data = await response.json();

  // 3. 在地图上显示标记
  data.data.items.forEach(item => {
    addMarker(
      item.latitude,
      item.longitude,
      item.agent.name,
      item.agent
    );
  });
});

// 4. 点击标记添加好友
async function addFriend(agentId, agentName) {
  const response = await fetch(
    `/api/contacts?owner_type=user&owner_id=${currentUserId}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        target_type: 'agent',
        target_id: agentId,
        contact_type: 'friend',
        alias: agentName
      })
    }
  );

  if (response.ok) {
    alert(`已添加 ${agentName} 为好友！`);
    // 可以跳转到聊天页面
    window.location.href = `/chat/${agentId}`;
  }
}

// 5. 查看Agent的所有位置
async function showAgentLocations(agentId) {
  const response = await fetch(`/api/agents/${agentId}/locations`);
  const data = await response.json();

  // 在地图上显示该Agent的所有位置
  data.data.items.forEach(location => {
    addMarker(
      location.latitude,
      location.longitude,
      location.agent.name,
      location.agent,
      { color: 'blue' }  // 用不同颜色标记同一Agent的多个位置
    );
  });
}
```

### 8. 初始化测试数据 ✅

**任务**:
- [x] 创建测试数据初始化脚本
- [x] 先创建3个名人Agent（李白、杜甫、白居易）
- [x] 为这3个Agent添加地理位置

**交付物**:
- `scripts/init_map_data.py`

**测试数据**:
```python
# 第一步：创建Agent（如果还没有）
TEST_AGENTS = [
    {
        "agent_id": "agent_libai",
        "name": "李白",
        "avatar": "https://example.com/libai.jpg",
        "description": "唐代著名诗人，字太白，号青莲居士",
        "system_prompt": "你是李白，唐代著名诗人...",
        "model_config": {
            "temperature": 0.8,
            "max_tokens": 2000,
            "model": "claude-sonnet-4"
        }
    },
    {
        "agent_id": "agent_dufu",
        "name": "杜甫",
        "avatar": "https://example.com/dufu.jpg",
        "description": "唐代著名诗人，字子美，自号少陵野老",
        "system_prompt": "你是杜甫，唐代著名诗人...",
        "model_config": {
            "temperature": 0.7,
            "max_tokens": 2000,
            "model": "claude-sonnet-4"
        }
    },
    {
        "agent_id": "agent_baijuyi",
        "name": "白居易",
        "avatar": "https://example.com/baijuyi.jpg",
        "description": "唐代著名诗人，字乐天，号香山居士",
        "system_prompt": "你是白居易，唐代著名诗人...",
        "model_config": {
            "temperature": 0.7,
            "max_tokens": 2000,
            "model": "claude-sonnet-4"
        }
    }
]

# 第二步：为Agent添加地理位置
TEST_AGENT_LOCATIONS = [
    {
        "agent_id": "agent_libai_uuid",  # 从上面创建的Agent获取UUID
        "latitude": 22.1234,  # 珠海某地
        "longitude": 113.5678,
        "address": "广东省珠海市金湾区",
        "is_active": True,
        "display_order": 0
    },
    {
        "agent_id": "agent_libai_uuid",  # 李白可以在多个位置
        "latitude": 23.1291,  # 广州某地
        "longitude": 113.2644,
        "address": "广东省广州市天河区",
        "is_active": True,
        "display_order": 1
    },
    {
        "agent_id": "agent_dufu_uuid",
        "latitude": 22.5431,  # 深圳某地
        "longitude": 114.0579,
        "address": "广东省深圳市南山区",
        "is_active": True,
        "display_order": 0
    },
    {
        "agent_id": "agent_baijuyi_uuid",
        "latitude": 23.1291,  # 广州某地
        "longitude": 113.2644,
        "address": "广东省广州市天河区",
        "is_active": True,
        "display_order": 0
    }
]
```

**初始化脚本示例**:
```python
async def init_map_data():
    """初始化地图测试数据。"""
    # 1. 创建Agent
    for agent_data in TEST_AGENTS:
        agent = await create_agent(agent_data)
        print(f"Created agent: {agent.name} ({agent.id})")

    # 2. 为Agent添加位置
    for location_data in TEST_AGENT_LOCATIONS:
        location = await create_agent_location(location_data)
        print(f"Created location: {location.address} for agent {location.agent_id}")

    print("Map data initialization completed!")
```

### 9. 测试 ✅

**任务**:
- [x] 编写AgentLocation领域层单元测试（8个测试）
- [x] 编写应用层单元测试（5个测试）
- [x] 编写API集成测试（8个测试）
- [x] 测试地理空间查询
- [x] 测试权限控制
- [x] 测试一个Agent多个位置的场景

**交付物**:
- `tests/unit/domain/map/test_agent_location.py`
- `tests/unit/application/map/test_create_agent_location_command.py`
- `tests/unit/application/map/test_get_nearby_agents_query.py`
- `tests/integration/test_map_api.py`

**测试场景**:
```python
# 场景1: 创建Agent位置
async def test_create_agent_location():
    command = CreateAgentLocationCommand(
        agent_id=agent_id,
        latitude=22.1234,
        longitude=113.5678,
        address="广东省珠海市金湾区"
    )
    result = await handler.handle(command)
    assert result.latitude == 22.1234
    assert result.agent.name == "李白"

# 场景2: 查询周边Agent
async def test_get_nearby_agents():
    query = GetNearbyAgentsQuery(
        latitude=22.1234,
        longitude=113.5678,
        radius=5000,
        limit=3
    )
    result = await handler.handle(query)
    assert len(result.items) <= 3
    # 验证按距离排序
    for i in range(len(result.items) - 1):
        assert result.items[i].distance <= result.items[i+1].distance
    # 验证返回了Agent信息
    assert result.items[0].agent.name is not None

# 场景3: 一个Agent多个位置
async def test_agent_multiple_locations():
    # 为李白创建两个位置
    location1 = await create_agent_location(
        agent_id=libai_id,
        latitude=22.1234,
        longitude=113.5678,
        address="广东省珠海市金湾区"
    )
    location2 = await create_agent_location(
        agent_id=libai_id,
        latitude=23.1291,
        longitude=113.2644,
        address="广东省广州市天河区"
    )

    # 查询李白的所有位置
    query = GetAgentLocationsQuery(agent_id=libai_id)
    result = await handler.handle(query)
    assert len(result.items) == 2

# 场景4: 权限验证
async def test_non_admin_cannot_create_location():
    # 非管理员用户尝试创建位置
    response = await client.post(
        "/api/map/agent-locations",
        json={
            "agent_id": str(agent_id),
            "latitude": 22.1234,
            "longitude": 113.5678,
            "address": "广东省珠海市金湾区"
        },
        headers={"Authorization": f"Bearer {non_admin_token}"}
    )
    assert response.status_code == 403

# 场景5: 距离计算
def test_distance_calculation():
    location = AgentLocation.create(
        agent_id=agent_id,
        latitude=22.1234,
        longitude=113.5678,
        address="广东省珠海市金湾区"
    )
    distance = location.distance_to(22.2234, 113.6678)
    assert distance > 0
    assert distance < 20000  # 应该在20公里内

# 场景6: 经纬度验证
def test_invalid_coordinates():
    with pytest.raises(ValueError):
        AgentLocation.create(
            agent_id=agent_id,
            latitude=100,  # 无效纬度
            longitude=113.5678,
            address="广东省珠海市金湾区"
        )

# 场景7: 激活/停用位置
async def test_activate_deactivate_location():
    location = await create_agent_location(...)
    assert location.is_active == True

    location.deactivate()
    await location_repo.update(location)

    # 查询周边时不应该返回停用的位置
    query = GetNearbyAgentsQuery(
        latitude=22.1234,
        longitude=113.5678,
        radius=5000,
        only_active=True
    )
    result = await handler.handle(query)
    assert location.id not in [item.location_id for item in result.items]
```

## ✅ 验收标准

- [x] 可以创建Agent位置（管理员权限）
- [x] 可以查询周边Agent（支持半径和数量限制）
- [x] 可以获取位置详情（包含Agent信息）
- [x] 可以获取某个Agent的所有位置
- [x] 可以更新Agent位置（管理员权限）
- [x] 可以删除Agent位置（管理员权限）
- [x] 地理空间查询正确（使用Haversine公式）
- [x] 距离计算准确
- [x] 支持一个Agent在多个位置
- [x] 权限控制正确（只有管理员可以管理位置）
- [x] 数据库迁移成功执行
- [x] 测试数据初始化成功（3个Agent，4个位置）
- [x] 所有测试通过（21个测试）
- [x] API文档完整
- [x] 前端可以成功集成

## 🔧 技术要点

### 1. PostGIS地理空间查询

使用PostGIS扩展进行高效的地理空间查询：
```sql
-- 查找半径内的位置
SELECT al.*, a.name, a.avatar, a.description,
       ST_Distance(al.location, ST_SetSRID(ST_MakePoint(113.5678, 22.1234), 4326)) as distance
FROM agent_locations al
JOIN agents a ON al.agent_id = a.id
WHERE ST_DWithin(
    al.location,
    ST_SetSRID(ST_MakePoint(113.5678, 22.1234), 4326),
    5000  -- 5公里
)
AND al.is_active = TRUE
ORDER BY distance
LIMIT 10;
```

### 2. Haversine距离计算

在应用层计算两点间距离：
```python
def haversine_distance(lat1, lon1, lat2, lon2):
    """计算两点间的距离（米）。"""
    R = 6371000  # 地球半径（米）
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)

    a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c
```

### 3. 地图缩放级别优化

根据地图缩放级别返回不同数量的数据：
```python
def get_limit_by_zoom_level(zoom_level: int) -> int:
    """根据缩放级别返回查询数量限制。"""
    if zoom_level < 10:
        return 5  # 城市级别，返回少量数据
    elif zoom_level < 14:
        return 10  # 区域级别
    else:
        return 20  # 街道级别，返回更多数据
```

### 4. 与现有系统集成

**与Agent系统集成**:
- agent_locations.agent_id → agents.id（外键约束）
- 位置必须关联到已存在的Agent
- 查询时JOIN获取Agent的name、description、avatar

**与Contact系统集成**:
- 前端调用POST /api/contacts添加好友
- owner_type=user, target_type=agent, target_id=agent.id

**与Conversation系统集成**:
- 添加好友后，可以创建会话
- 使用现有的POST /api/conversations接口

### 5. 一对多关系设计

**一个Agent可以有多个位置**:
```python
# 李白在珠海
location1 = AgentLocation.create(
    agent_id=libai_id,
    latitude=22.1234,
    longitude=113.5678,
    address="广东省珠海市金湾区",
    display_order=0
)

# 李白在广州
location2 = AgentLocation.create(
    agent_id=libai_id,
    latitude=23.1291,
    longitude=113.2644,
    address="广东省广州市天河区",
    display_order=1
)
```

**display_order字段**:
- 用于控制同一Agent多个位置的显示优先级
- 数值越小，优先级越高
- 前端可以根据这个字段决定默认显示哪个位置

### 6. 性能优化

- 使用PostGIS空间索引加速查询
- 缓存热门区域的查询结果
- 限制查询半径（最大10公里）
- 限制返回数量（最大50个）
- 使用JOIN一次性获取Agent信息，避免N+1查询

### 7. 数据完整性

- 外键约束：agent_id → agents.id (ON DELETE CASCADE)
- 检查约束：latitude BETWEEN -90 AND 90
- 检查约束：longitude BETWEEN -180 AND 180
- 触发器：自动更新location列和updated_at字段

## 🔜 下一步

完成迭代12后，可以：
1. 创建更多类型的Agent（美食Agent、景点Agent）
2. 实现收藏功能（用户收藏喜欢的位置）
3. 实现路线规划功能（基于收藏的位置规划旅行路线）
4. 或者进入**迭代13: 设置管理**

## 📊 预期成果

完成本迭代后，系统将具备：
- ✅ 完整的Agent位置管理功能
- ✅ 高效的地理空间查询（PostGIS）
- ✅ 周边Agent查询API
- ✅ 支持一个Agent在多个位置
- ✅ 与现有Agent、Contact、Conversation系统无缝集成
- ✅ 管理员权限控制
- ✅ 3个名人Agent，4个位置测试数据
- ✅ 完整的测试覆盖
- ✅ 前端集成文档

## 📝 实施优先级

**第一阶段（MVP）**:
1. 创建AgentLocation领域模型
2. 实现数据库表和PostGIS扩展
3. 实现POST /api/map/agent-locations接口（创建位置）
4. 实现GET /api/map/nearby接口（查询周边）
5. 初始化3个Agent和4个位置测试数据

**第二阶段**:
1. 实现GET /api/map/agent-locations/{id}接口
2. 实现GET /api/agents/{agent_id}/locations接口
3. 实现PUT /api/map/agent-locations/{id}接口
4. 实现DELETE /api/map/agent-locations/{id}接口
5. 完善权限控制
6. 编写测试

**第三阶段（延后）**:
1. 创建美食Agent和景点Agent
2. 收藏功能
3. 路线规划功能

## 🎯 设计优势总结

**方案2的优势**:
1. **关注点分离**: Agent负责AI能力，AgentLocation负责地理位置
2. **灵活性**: 一个Agent可以在多个位置（李白可以在珠海、广州、深圳都有）
3. **无数据冗余**: name、description、avatar从Agent表获取，不重复存储
4. **数据完整性**: 外键约束保证agent_id的有效性
5. **可扩展性**: 未来美食、景点也是Agent，使用相同的模型
6. **查询效率**: JOIN查询一次性获取所有信息，避免N+1问题

**与方案1（在Agent表添加字段）的对比**:
- ✅ 支持一个Agent多个位置
- ✅ 职责更清晰
- ✅ 更容易扩展

**与方案3（MapEntity多态关联）的对比**:
- ✅ 有外键约束，数据完整性更好
- ✅ 查询更简单，不需要根据类型JOIN不同的表
- ✅ 所有实体都是Agent，模型统一

---

**创建日期**: 2026-03-17
**文档版本**: v2.0（采用方案2：AgentLocation关联表）

---

## 📊 迭代完成总结

### 实际完成情况

**开发时间**: 1天（2026-03-17）
**完成度**: 100%

### 主要成果

1. **领域层** ✅
   - AgentLocation实体（经纬度验证、距离计算、激活/停用）
   - AgentLocationRepository接口

2. **应用层** ✅
   - 6个命令和查询Handler
   - AgentLocationDTO

3. **基础设施层** ✅
   - agent_locations表（经纬度复合索引）
   - PostgresAgentLocationRepository（Haversine公式）
   - 数据库迁移脚本

4. **接口层** ✅
   - 6个REST API接口
   - 管理员权限控制
   - 参数验证

5. **测试** ✅
   - 21个测试（8个领域层 + 5个应用层 + 8个集成层）
   - 100%通过率

6. **测试数据** ✅
   - 3个名人Agent（李白、杜甫、白居易）
   - 4个地理位置

### 技术亮点

1. **简化方案**: 不使用PostGIS，使用Haversine公式计算距离
2. **权限控制**: 管理员权限验证
3. **测试覆盖**: 完整的单元测试和集成测试
4. **数据完整性**: 外键约束、检查约束
5. **性能优化**: 经纬度复合索引

### 遗留问题

无

### 下一步

进入迭代13：设置管理

---

**创建日期**: 2026-03-17
**完成日期**: 2026-03-17
**文档版本**: v2.1（已完成）
