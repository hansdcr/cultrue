"""集成测试配置文件。

提供集成测试所需的fixtures和环境配置。
"""

import pytest
import pytest_asyncio

from src.infrastructure.config import settings
from src.infrastructure.persistence.database import init_database, close_database, get_db_session
from src.application.realtime.services.connection_manager import ConnectionManager
from src.application.realtime.services.message_push_service import MessagePushService
from src.application.realtime.services.online_status_service import OnlineStatusService
from src.application.shared.events.event_bus import EventBus
from src.application.realtime.handlers.message_sent_handler import MessageSentEventHandler
from src.application.realtime.handlers.message_deleted_handler import MessageDeletedEventHandler
from src.infrastructure.persistence.repositories.postgres_conversation_repository import PostgresConversationRepository
from src.infrastructure.persistence.repositories.postgres_participant_repository import PostgresParticipantRepository
from src.interfaces.websocket import endpoints as ws_endpoints
from src.interfaces.api.rest import message


# 全局标志，确保数据库只初始化一次
_db_initialized = False


def pytest_configure(config):
    """Pytest配置钩子，在所有测试开始前初始化数据库。"""
    global _db_initialized
    if not _db_initialized:
        init_database(
            database_url=settings.database_url,
            pool_size=5,
            max_overflow=5,
        )
        _db_initialized = True


@pytest.fixture(scope="function", autouse=True)
def setup_websocket_services():
    """设置WebSocket相关服务（同步fixture）。

    这个fixture会在每个测试前初始化所有WebSocket依赖，
    解决TestClient不触发lifespan的问题。
    """
    # 注意：这是一个同步fixture，但它设置的是全局变量
    # 实际的数据库操作会在测试运行时通过依赖注入进行

    # 创建服务实例
    connection_manager = ConnectionManager()
    event_bus = EventBus()

    # 设置WebSocket端点依赖（使用None作为占位符，实际使用时会通过依赖注入获取）
    ws_endpoints.set_connection_manager(connection_manager)
    ws_endpoints.set_online_status_service(None)  # 暂时设为None
    ws_endpoints.set_conversation_repo(None)  # 暂时设为None

    # 设置message路由的EventBus
    message.set_event_bus(event_bus)

    yield

    # 清理：重置全局变量
    ws_endpoints.set_connection_manager(None)
    ws_endpoints.set_online_status_service(None)
    ws_endpoints.set_conversation_repo(None)
    message.set_event_bus(None)
