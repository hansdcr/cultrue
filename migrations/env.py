"""Alembic迁移环境配置。

配置数据库连接和模型元数据。
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from src.infrastructure.config import settings
from src.infrastructure.persistence.database import Base
# 导入所有模型以便Alembic可以检测到它们
import src.infrastructure.persistence.models  # noqa: F401

# Alembic配置对象
config = context.config

# 配置Python日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置数据库URL（从配置读取，转换为同步URL用于Alembic）
database_url = settings.database_url
# 将asyncpg替换为psycopg2用于Alembic迁移
if "postgresql+asyncpg" in database_url:
    database_url = database_url.replace("postgresql+asyncpg", "postgresql")
config.set_main_option("sqlalchemy.url", database_url)

# 设置模型元数据（用于autogenerate）
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """在离线模式下运行迁移。

    此模式仅使用URL配置上下文，不需要Engine。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在在线模式下运行迁移。

    此模式创建Engine并将连接与上下文关联。
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
