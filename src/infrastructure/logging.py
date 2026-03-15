"""日志配置模块。

提供统一的日志配置和管理。
"""

import logging
import sys
from pathlib import Path
from typing import Any

from src.infrastructure.config import settings


def setup_logging() -> None:
    """配置应用日志系统。

    根据配置文件设置日志级别、格式和输出目标。
    """
    # 创建logs目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 配置日志级别
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # 配置日志格式
    if settings.log_format == "json":
        log_format = (
            '{"time":"%(asctime)s","level":"%(levelname)s",'
            '"name":"%(name)s","message":"%(message)s"}'
        )
    else:
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )

    # 配置根日志记录器
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            # 控制台输出
            logging.StreamHandler(sys.stdout),
            # 文件输出
            logging.FileHandler(
                log_dir / "app.log",
                encoding="utf-8",
            ),
        ],
    )

    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器。

    Args:
        name: 日志记录器名称，通常使用__name__

    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)
