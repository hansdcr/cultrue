"""应用配置管理模块。

使用pydantic-settings从环境变量加载配置。
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类。

    从环境变量或.env文件加载配置。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = Field(default="Cultrue", description="应用名称")
    app_env: str = Field(default="development", description="运行环境")
    debug: bool = Field(default=True, description="调试模式")
    api_version: str = Field(default="v1", description="API版本")

    # Server
    host: str = Field(default="0.0.0.0", description="服务器地址")
    port: int = Field(default=8000, description="服务器端口")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/cultrue",
        description="数据库连接URL",
    )
    database_pool_size: int = Field(default=20, description="数据库连接池大小")
    database_max_overflow: int = Field(default=10, description="数据库连接池最大溢出")

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        description="JWT密钥",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT算法")
    jwt_access_token_expire_minutes: int = Field(
        default=15, description="访问令牌过期时间（分钟）"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, description="刷新令牌过期时间（天）"
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis连接URL"
    )
    redis_password: str = Field(default="", description="Redis密码")

    # Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1", description="Celery消息代理URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2", description="Celery结果后端URL"
    )

    # Agent Service
    agent_service_url: str = Field(
        default="http://localhost:8001", description="Agent服务URL"
    )
    agent_service_timeout: int = Field(default=30, description="Agent服务超时时间（秒）")

    # CORS
    cors_origins: str = Field(
        default="*",
        description="允许的CORS源（逗号分隔，* 表示全部）",
    )
    cors_allow_credentials: bool = Field(default=False, description="允许CORS凭证")

    # Logging
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(default="json", description="日志格式")

    def get_cors_origins_list(self) -> list[str]:
        """获取CORS源列表。"""
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


# 全局配置实例
settings = Settings()
