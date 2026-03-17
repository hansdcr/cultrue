"""Unit tests for ConnectionManager."""
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from src.application.realtime.services.connection_manager import ConnectionManager
from src.domain.shared.value_objects.actor import Actor
from src.domain.shared.enums.actor_type import ActorType
from src.domain.realtime.enums.connection_status import ConnectionStatus


@pytest.fixture
def connection_manager():
    """创建ConnectionManager实例。"""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """创建模拟的WebSocket连接。"""
    ws = MagicMock()
    ws.client = MagicMock()
    ws.client.host = "127.0.0.1"
    return ws


@pytest.fixture
def user_actor():
    """创建User Actor。"""
    return Actor.from_user(UUID("12345678-1234-1234-1234-123456789012"))


@pytest.fixture
def agent_actor():
    """创建Agent Actor。"""
    return Actor.from_agent(UUID("87654321-4321-4321-4321-210987654321"))


@pytest.mark.asyncio
async def test_connect(connection_manager, mock_websocket, user_actor):
    """测试连接注册。"""
    # 注册连接
    connection = await connection_manager.connect(
        mock_websocket,
        user_actor,
        {"device": "mobile"}
    )

    # 验证连接状态
    assert connection.actor == user_actor
    assert connection.status == ConnectionStatus.CONNECTED
    assert connection.metadata["device"] == "mobile"

    # 验证在线状态
    assert connection_manager.is_online(user_actor)

    # 验证连接列表
    connections = connection_manager.get_connections(user_actor)
    assert len(connections) == 1
    assert mock_websocket in connections


@pytest.mark.asyncio
async def test_disconnect(connection_manager, mock_websocket, user_actor):
    """测试连接注销。"""
    # 先注册连接
    await connection_manager.connect(mock_websocket, user_actor)

    # 注销连接
    await connection_manager.disconnect(mock_websocket)

    # 验证在线状态
    assert not connection_manager.is_online(user_actor)

    # 验证连接列表
    connections = connection_manager.get_connections(user_actor)
    assert len(connections) == 0


@pytest.mark.asyncio
async def test_multiple_device_connections(
    connection_manager,
    user_actor
):
    """测试多设备连接。"""
    # 创建两个WebSocket连接
    ws1 = MagicMock()
    ws2 = MagicMock()

    # 注册两个连接
    await connection_manager.connect(ws1, user_actor)
    await connection_manager.connect(ws2, user_actor)

    # 验证在线状态
    assert connection_manager.is_online(user_actor)

    # 验证连接数量
    connections = connection_manager.get_connections(user_actor)
    assert len(connections) == 2
    assert ws1 in connections
    assert ws2 in connections

    # 断开一个连接
    await connection_manager.disconnect(ws1)

    # 验证仍然在线
    assert connection_manager.is_online(user_actor)

    # 验证连接数量
    connections = connection_manager.get_connections(user_actor)
    assert len(connections) == 1
    assert ws2 in connections

    # 断开第二个连接
    await connection_manager.disconnect(ws2)

    # 验证离线
    assert not connection_manager.is_online(user_actor)


@pytest.mark.asyncio
async def test_update_heartbeat(connection_manager, mock_websocket, user_actor):
    """测试心跳更新。"""
    # 注册连接
    connection = await connection_manager.connect(mock_websocket, user_actor)
    initial_heartbeat = connection.last_heartbeat_at

    # 等待一小段时间
    await asyncio.sleep(0.1)

    # 更新心跳
    await connection_manager.update_heartbeat(mock_websocket)

    # 验证心跳时间已更新
    assert connection.last_heartbeat_at > initial_heartbeat


@pytest.mark.asyncio
async def test_cleanup_dead_connections(connection_manager, user_actor):
    """测试清理僵尸连接。"""
    # 创建WebSocket连接
    ws = MagicMock()

    # 注册连接
    connection = await connection_manager.connect(ws, user_actor)

    # 模拟连接超时（修改last_heartbeat_at）
    from datetime import datetime, timezone, timedelta
    connection.last_heartbeat_at = datetime.now(timezone.utc) - timedelta(seconds=70)

    # 模拟WebSocket的close方法
    ws.close = AsyncMock()

    # 执行清理
    count = await connection_manager.cleanup_dead_connections(timeout_seconds=60)

    # 验证清理了一个连接
    assert count == 1

    # 验证连接已断开
    assert not connection_manager.is_online(user_actor)


@pytest.mark.asyncio
async def test_different_actor_types(
    connection_manager,
    user_actor,
    agent_actor
):
    """测试不同类型的Actor。"""
    # 创建两个WebSocket连接
    ws_user = MagicMock()
    ws_agent = MagicMock()

    # 注册User和Agent连接
    await connection_manager.connect(ws_user, user_actor)
    await connection_manager.connect(ws_agent, agent_actor)

    # 验证两者都在线
    assert connection_manager.is_online(user_actor)
    assert connection_manager.is_online(agent_actor)

    # 验证连接隔离
    user_connections = connection_manager.get_connections(user_actor)
    agent_connections = connection_manager.get_connections(agent_actor)

    assert len(user_connections) == 1
    assert len(agent_connections) == 1
    assert ws_user in user_connections
    assert ws_agent in agent_connections
    assert ws_user not in agent_connections
    assert ws_agent not in user_connections
