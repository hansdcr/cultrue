"""验证Agent数据。"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# 数据库连接URL
DATABASE_URL = "postgresql+asyncpg://agent:agent123@localhost:5432/cultrue"


async def verify_agents():
    """验证Agent数据。"""
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        print("检查Agent数据...")
        print()

        # 查询所有Agent
        result = await conn.execute(text("""
            SELECT agent_id, name, description, api_key_prefix, is_active
            FROM agents
            ORDER BY agent_id
        """))
        agents = result.fetchall()

        if agents:
            print(f"✓ 找到 {len(agents)} 个Agent")
            print()
            for agent in agents:
                print(f"Agent ID: {agent[0]}")
                print(f"  名称: {agent[1]}")
                print(f"  描述: {agent[2][:50]}..." if len(agent[2]) > 50 else f"  描述: {agent[2]}")
                print(f"  API Key前缀: {agent[3]}")
                print(f"  状态: {'激活' if agent[4] else '停用'}")
                print()
        else:
            print("✗ 未找到Agent数据")

    await engine.dispose()
    print("验证完成！")


if __name__ == "__main__":
    asyncio.run(verify_agents())
