"""连接清理后台任务。

定期清理超时的WebSocket连接。
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.application.realtime.services.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class ConnectionCleanupTask:
    """连接清理后台任务。"""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        interval_seconds: int = 30,
        timeout_seconds: int = 60,
    ):
        """初始化连接清理任务。

        Args:
            connection_manager: 连接管理器
            interval_seconds: 清理间隔（秒）
            timeout_seconds: 连接超时时间（秒）
        """
        self.connection_manager = connection_manager
        self.interval_seconds = interval_seconds
        self.timeout_seconds = timeout_seconds
        self.scheduler = AsyncIOScheduler()

    async def cleanup(self) -> None:
        """执行清理任务。"""
        try:
            count = await self.connection_manager.cleanup_dead_connections(
                self.timeout_seconds
            )
            if count > 0:
                logger.info(f"Cleaned up {count} dead connections")
        except Exception as e:
            logger.error(f"Connection cleanup error: {e}", exc_info=True)

    def start(self) -> None:
        """启动清理任务。"""
        self.scheduler.add_job(
            self.cleanup,
            "interval",
            seconds=self.interval_seconds,
        )
        self.scheduler.start()
        logger.info(
            f"Connection cleanup task started "
            f"(interval={self.interval_seconds}s, timeout={self.timeout_seconds}s)"
        )

    def stop(self) -> None:
        """停止清理任务。"""
        self.scheduler.shutdown()
        logger.info("Connection cleanup task stopped")
