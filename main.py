"""Cultrue Backend Application.

多方通信平台后端服务，支持用户、Agent之间的通信。
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.config import settings
from src.infrastructure.persistence.database import close_database, init_database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理。

    Args:
        app: FastAPI应用实例

    Yields:
        None
    """
    # 启动时初始化数据库
    init_database(
        database_url=settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
    )
    print(f"✅ Database initialized: {settings.database_url}")

    yield

    # 关闭时清理资源
    await close_database()
    print("✅ Database connection closed")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """根路径健康检查。

    Returns:
        包含应用信息的字典
    """
    return {
        "app": settings.app_name,
        "version": settings.api_version,
        "status": "running",
        "environment": settings.app_env,
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """健康检查端点。

    Returns:
        健康状态信息
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

