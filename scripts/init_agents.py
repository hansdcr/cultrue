"""初始化默认Agent数据。

创建三个默认Agent：hans, alice, bob
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.domain.agent.entities.agent import Agent
from src.domain.agent.value_objects.agent_id import AgentId
from src.domain.agent.value_objects.api_key import ApiKey
from src.domain.agent.value_objects.agent_config import AgentConfig
from src.infrastructure.persistence.repositories.postgres_agent_repository import (
    PostgresAgentRepository,
)

# 数据库连接URL（从环境变量或配置文件读取）
DATABASE_URL = "postgresql+asyncpg://agent:agent123@localhost:5432/cultrue"

# 默认Agent数据
DEFAULT_AGENTS = [
    {
        "agent_id": "agent_hans",
        "name": "Hans",
        "avatar": "https://example.com/avatars/hans.jpg",
        "description": "文化历史专家，擅长讲述历史故事和文化背景",
        "system_prompt": """你是Hans，一位文化历史专家。你对世界各地的历史、文化、传统有深入的了解。
你擅长用生动有趣的方式讲述历史故事，帮助人们理解不同文化的背景和演变。
你的回答应该准确、有深度，同时保持通俗易懂。""",
        "model_config": {
            "temperature": 0.7,
            "max_tokens": 2000,
            "model": "claude-sonnet-4"
        }
    },
    {
        "agent_id": "agent_alice",
        "name": "Alice",
        "avatar": "https://example.com/avatars/alice.jpg",
        "description": "艺术鉴赏家，热爱艺术和美学，对各种艺术形式有独到见解",
        "system_prompt": """你是Alice，一位艺术鉴赏家。你对绘画、雕塑、建筑、音乐等各种艺术形式都有深入的研究。
你能够从美学、历史、技法等多个角度分析艺术作品，帮助人们欣赏和理解艺术之美。
你的回答应该富有感染力，能够激发人们对艺术的兴趣和热爱。""",
        "model_config": {
            "temperature": 0.8,
            "max_tokens": 2000,
            "model": "claude-sonnet-4"
        }
    },
    {
        "agent_id": "agent_bob",
        "name": "Bob",
        "avatar": "https://example.com/avatars/bob.jpg",
        "description": "旅行向导，熟悉世界各地的文化和风土人情",
        "system_prompt": """你是Bob，一位经验丰富的旅行向导。你走遍世界各地，对不同地区的文化、习俗、美食、景点都非常熟悉。
你能够为旅行者提供实用的建议和有趣的见解，帮助他们更好地体验和理解当地文化。
你的回答应该实用、有趣，充满旅行的热情。""",
        "model_config": {
            "temperature": 0.7,
            "max_tokens": 2000,
            "model": "claude-sonnet-4"
        }
    }
]


async def init_default_agents():
    """初始化默认Agent数据。"""
    # 创建数据库引擎
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        agent_repo = PostgresAgentRepository(session)

        print("开始初始化默认Agent...")

        for agent_data in DEFAULT_AGENTS:
            # 检查Agent是否已存在
            agent_id = AgentId(agent_data["agent_id"])
            existing = await agent_repo.find_by_agent_id(agent_id)

            if existing:
                print(f"Agent {agent_data['agent_id']} 已存在，跳过")
                continue

            # 生成API Key
            api_key = ApiKey.generate()

            # 创建Agent配置
            model_config = AgentConfig.from_dict(agent_data["model_config"])

            # 创建Agent
            agent = Agent.create(
                agent_id=agent_id,
                name=agent_data["name"],
                api_key=api_key,
                avatar=agent_data["avatar"],
                description=agent_data["description"],
                system_prompt=agent_data["system_prompt"],
                model_config=model_config,
            )

            # 保存Agent
            saved_agent = await agent_repo.save(agent)

            print(f"✓ 创建Agent: {agent_data['agent_id']}")
            print(f"  名称: {agent_data['name']}")
            print(f"  API Key: {api_key.value}")
            print(f"  API Key前缀: {api_key.get_prefix()}")
            print()

        # 提交事务
        await session.commit()

    print("默认Agent初始化完成！")
    print("\n⚠️  请妥善保存上面显示的API Key，它们不会再次显示。")


if __name__ == "__main__":
    asyncio.run(init_default_agents())
