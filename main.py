"""Cultrue Backend Application.

多方通信平台后端服务，支持用户、Agent之间的通信。
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.config import settings
from src.infrastructure.logging import get_logger, setup_logging
from src.infrastructure.persistence.database import close_database, init_database
from src.interfaces.api.exception_handlers import register_exception_handlers
from src.interfaces.api.schemas.response import ApiResponse

# 配置日志
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理。

    Args:
        app: FastAPI应用实例

    Yields:
        None
    """
    # 启动时初始化数据库
    logger.info("Initializing database connection...")
    init_database(
        database_url=settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
    )
    logger.info(f"Database initialized: {settings.database_url}")

    yield

    # 关闭时清理资源
    logger.info("Closing database connection...")
    await close_database()
    logger.info("Database connection closed")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# 注册异常处理器
register_exception_handlers(app)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=ApiResponse[dict[str, str]])
async def root() -> ApiResponse[dict[str, str]]:
    """根路径健康检查。

    Returns:
        包含应用信息的响应
    """
    logger.info("Root endpoint accessed")
    return ApiResponse.success(
        data={
            "app": settings.app_name,
            "version": settings.api_version,
            "status": "running",
            "environment": settings.app_env,
        }
    )


@app.get("/health", response_model=ApiResponse[dict[str, str]])
async def health_check() -> ApiResponse[dict[str, str]]:
    """健康检查端点。

    Returns:
        健康状态信息
    """
    logger.debug("Health check endpoint accessed")
    return ApiResponse.success(data={"status": "healthy"})


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting {settings.app_name} on {settings.host}:{settings.port}")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

