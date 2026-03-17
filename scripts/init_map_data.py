"""初始化地图测试数据。

创建3个名人Agent（李白、杜甫、白居易）和4个地理位置。
"""
import asyncio
import sys
from pathlib import Path
from uuid import UUID

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.domain.agent.entities.agent import Agent
from src.domain.agent.value_objects.agent_id import AgentId
from src.domain.agent.value_objects.api_key import ApiKey
from src.domain.agent.value_objects.agent_config import AgentConfig
from src.domain.map.entities.agent_location import AgentLocation
from src.infrastructure.persistence.repositories.postgres_agent_repository import (
    PostgresAgentRepository,
)
from src.infrastructure.persistence.repositories.postgres_agent_location_repository import (
    PostgresAgentLocationRepository,
)

# 数据库连接URL（从环境变量或配置文件读取）
DATABASE_URL = "postgresql+asyncpg://agent:agent123@localhost:5432/cultrue"

# 测试Agent数据
TEST_AGENTS = [
    {
        "agent_id": "agent_libai",
        "name": "李白",
        "avatar": "https://example.com/avatars/libai.jpg",
        "description": "唐代著名诗人，字太白，号青莲居士",
        "system_prompt": """你是李白，唐代著名诗人。你豪放不羁，才华横溢，被誉为"诗仙"。
你的诗歌想象丰富，气势磅礴，充满浪漫主义色彩。
你热爱自然，喜欢饮酒作诗，追求自由洒脱的生活。
在回答时，请展现你的诗人气质和豪迈性格。""",
        "model_config": {
            "temperature": 0.8,
            "max_tokens": 2000,
            "model": "claude-sonnet-4"
        }
    },
    {
        "agent_id": "agent_dufu",
        "name": "杜甫",
        "avatar": "https://example.com/avatars/dufu.jpg",
        "description": "唐代著名诗人，字子美，自号少陵野老",
        "system_prompt": """你是杜甫，唐代著名诗人。你忧国忧民，诗风沉郁顿挫，被誉为"诗圣"。
你的诗歌反映社会现实，关注民生疾苦，具有强烈的人文关怀。
你严谨认真，对诗歌创作精益求精，被后世尊为"诗史"。
在回答时，请展现你的深沉情怀和社会责任感。""",
        "model_config": {
            "temperature": 0.7,
            "max_tokens": 2000,
            "model": "claude-sonnet-4"
        }
    },
    {
        "agent_id": "agent_baijuyi",
        "name": "白居易",
        "avatar": "https://example.com/avatars/baijuyi.jpg",
        "description": "唐代著名诗人，字乐天，号香山居士",
        "system_prompt": """你是白居易，唐代著名诗人。你主张"文章合为时而著，歌诗合为事而作"。
你的诗歌通俗易懂，贴近生活，深受百姓喜爱。
你性格温和，为官清廉，关心民生，是一位有社会责任感的诗人。
在回答时，请展现你的平易近人和对生活的热爱。""",
        "model_config": {
            "temperature": 0.7,
            "max_tokens": 2000,
            "model": "claude-sonnet-4"
        }
    }
]


async def init_map_data():
    """初始化地图测试数据。"""
    # 创建数据库引擎
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        agent_repo = PostgresAgentRepository(session)
        location_repo = PostgresAgentLocationRepository(session, agent_repo)

        print("=" * 60)
        print("开始初始化地图测试数据...")
        print("=" * 60)

        # 存储创建的Agent ID
        agent_ids = {}

        # 第一步：创建Agent
        print("\n第一步：创建3个名人Agent...")
        for agent_data in TEST_AGENTS:
            try:
                # 检查Agent是否已存在
                existing_agent = await agent_repo.find_by_agent_id(
                    AgentId(agent_data["agent_id"])
                )
                if existing_agent:
                    print(f"  ✓ Agent {agent_data['name']} 已存在，跳过创建")
                    agent_ids[agent_data["agent_id"]] = existing_agent.id
                    continue

                # 生成API Key
                api_key = ApiKey.generate()

                # 创建Agent实体
                agent = Agent.create(
                    agent_id=AgentId(agent_data["agent_id"]),
                    name=agent_data["name"],
                    avatar=agent_data["avatar"],
                    description=agent_data["description"],
                    system_prompt=agent_data["system_prompt"],
                    model_config=AgentConfig.from_dict(agent_data["model_config"]),
                    api_key=api_key,
                    created_by=None
                )

                # 保存Agent
                saved_agent = await agent_repo.save(agent)
                agent_ids[agent_data["agent_id"]] = saved_agent.id

                print(f"  ✓ 创建Agent: {saved_agent.name} (ID: {saved_agent.id})")

            except Exception as e:
                print(f"  ✗ 创建Agent {agent_data['name']} 失败: {e}")
                continue

        # 第二步：为Agent添加地理位置
        print("\n第二步：为Agent添加地理位置...")

        # 测试位置数据
        test_locations = [
            {
                "agent_id": agent_ids.get("agent_libai"),
                "latitude": 22.1234,  # 珠海某地
                "longitude": 113.5678,
                "address": "广东省珠海市金湾区",
                "is_active": True,
                "display_order": 0
            },
            {
                "agent_id": agent_ids.get("agent_libai"),  # 李白可以在多个位置
                "latitude": 23.1291,  # 广州某地
                "longitude": 113.2644,
                "address": "广东省广州市天河区",
                "is_active": True,
                "display_order": 1
            },
            {
                "agent_id": agent_ids.get("agent_dufu"),
                "latitude": 22.5431,  # 深圳某地
                "longitude": 114.0579,
                "address": "广东省深圳市南山区",
                "is_active": True,
                "display_order": 0
            },
            {
                "agent_id": agent_ids.get("agent_baijuyi"),
                "latitude": 23.1291,  # 广州某地
                "longitude": 113.2644,
                "address": "广东省广州市越秀区",
                "is_active": True,
                "display_order": 0
            }
        ]

        for location_data in test_locations:
            try:
                if not location_data["agent_id"]:
                    print(f"  ✗ 跳过位置创建（Agent不存在）: {location_data['address']}")
                    continue

                # 创建AgentLocation实体
                location = AgentLocation.create(
                    agent_id=location_data["agent_id"],
                    latitude=location_data["latitude"],
                    longitude=location_data["longitude"],
                    address=location_data["address"],
                    is_active=location_data["is_active"],
                    display_order=location_data["display_order"]
                )

                # 保存位置
                saved_location = await location_repo.save(location)

                # 获取Agent名称
                agent = await agent_repo.find_by_id(location_data["agent_id"])
                agent_name = agent.name if agent else "未知"

                print(f"  ✓ 创建位置: {saved_location.address} (Agent: {agent_name})")

            except Exception as e:
                print(f"  ✗ 创建位置失败 {location_data['address']}: {e}")
                continue

        print("\n" + "=" * 60)
        print("地图测试数据初始化完成！")
        print("=" * 60)
        print(f"\n创建了 {len(agent_ids)} 个Agent和 {len(test_locations)} 个位置")
        print("\n可以使用以下API测试：")
        print("  - GET /api/map/nearby?latitude=22.5&longitude=113.5&radius=50000")
        print("  - GET /api/map/agents/{agent_id}/locations")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_map_data())
