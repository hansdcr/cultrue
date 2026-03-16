"""验证数据库迁移是否成功。"""
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


async def verify_migration():
    """验证数据库迁移。"""
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        print("检查数据库表...")
        print()

        # 检查participants表
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'participants'
            ORDER BY ordinal_position
        """))
        participants_columns = result.fetchall()

        if participants_columns:
            print("✓ participants表存在")
            print("  字段:")
            for col in participants_columns:
                print(f"    - {col[0]}: {col[1]} (nullable: {col[2]})")
        else:
            print("✗ participants表不存在")

        print()

        # 检查contacts表
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'contacts'
            ORDER BY ordinal_position
        """))
        contacts_columns = result.fetchall()

        if contacts_columns:
            print("✓ contacts表存在")
            print("  字段:")
            for col in contacts_columns:
                print(f"    - {col[0]}: {col[1]} (nullable: {col[2]})")
        else:
            print("✗ contacts表不存在")

        print()

        # 检查agents表的新字段
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'agents'
            AND column_name IN ('api_key_prefix', 'api_key_hash')
            ORDER BY ordinal_position
        """))
        agent_new_columns = result.fetchall()

        if agent_new_columns:
            print("✓ agents表已更新")
            print("  新字段:")
            for col in agent_new_columns:
                print(f"    - {col[0]}: {col[1]} (nullable: {col[2]})")
        else:
            print("✗ agents表未更新")

        print()

        # 检查索引
        result = await conn.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename IN ('participants', 'contacts', 'agents')
            AND indexname LIKE 'idx_%'
            ORDER BY tablename, indexname
        """))
        indexes = result.fetchall()

        if indexes:
            print("✓ 索引已创建")
            print("  索引:")
            for idx in indexes:
                print(f"    - {idx[0]}")
        else:
            print("⚠ 未找到索引")

        print()

        # 检查约束
        result = await conn.execute(text("""
            SELECT conname, contype
            FROM pg_constraint
            WHERE conrelid IN (
                SELECT oid FROM pg_class
                WHERE relname IN ('participants', 'contacts')
            )
            ORDER BY conname
        """))
        constraints = result.fetchall()

        if constraints:
            print("✓ 约束已创建")
            print("  约束:")
            for con in constraints:
                con_type = {
                    'c': 'CHECK',
                    'f': 'FOREIGN KEY',
                    'p': 'PRIMARY KEY',
                    'u': 'UNIQUE'
                }.get(con[1], con[1])
                print(f"    - {con[0]}: {con_type}")

    await engine.dispose()
    print()
    print("数据库迁移验证完成！")


if __name__ == "__main__":
    asyncio.run(verify_migration())
