"""Integration tests for WebSocket connections.

Note: These tests require a properly configured test database and
the application to be fully initialized with the WebSocket connection manager.
They are currently marked as skipped and should be run in a proper
integration test environment.
"""
import pytest
from fastapi.testclient import TestClient
from uuid import UUID

from main import app
from src.infrastructure.security.jwt_service import jwt_service
from src.domain.agent.value_objects.api_key import ApiKey


pytestmark = pytest.mark.skip(reason="Integration tests require full database setup")


@pytest.fixture
def client():
    """创建测试客户端。"""
    return TestClient(app)


@pytest.fixture
def user_token():
    """创建User JWT token。"""
    user_id = "12345678-1234-1234-1234-123456789012"
    return jwt_service.create_access_token(user_id)


def test_websocket_connection_without_credentials(client):
    """测试没有认证信息的WebSocket连接。"""
    with pytest.raises(Exception):
        with client.websocket_connect("/ws"):
            pass


def test_websocket_connection_with_invalid_token(client):
    """测试使用无效token的WebSocket连接。"""
    with pytest.raises(Exception):
        with client.websocket_connect("/ws?token=invalid_token"):
            pass


def test_websocket_user_connection(client, user_token):
    """测试User通过JWT连接WebSocket。"""
    with client.websocket_connect(f"/ws?token={user_token}") as websocket:
        # 接收连接成功消息
        data = websocket.receive_json()
        assert data["type"] == "connection_established"
        assert data["data"]["actor_type"] == "user"
        assert "connection_id" in data["data"]
        assert "connected_at" in data["data"]


def test_websocket_heartbeat(client, user_token):
    """测试WebSocket心跳机制。"""
    with client.websocket_connect(f"/ws?token={user_token}") as websocket:
        # 接收连接成功消息
        websocket.receive_json()

        # 发送心跳
        websocket.send_json({"type": "ping"})

        # 接收心跳响应
        data = websocket.receive_json()
        assert data["type"] == "pong"
        assert "timestamp" in data


def test_websocket_unknown_message_type(client, user_token):
    """测试未知消息类型。"""
    with client.websocket_connect(f"/ws?token={user_token}") as websocket:
        # 接收连接成功消息
        websocket.receive_json()

        # 发送未知消息类型
        websocket.send_json({"type": "unknown"})

        # 接收错误响应
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Unknown message type" in data["message"]


def test_websocket_message_not_implemented(client, user_token):
    """测试消息发送功能（尚未实现）。"""
    with client.websocket_connect(f"/ws?token={user_token}") as websocket:
        # 接收连接成功消息
        websocket.receive_json()

        # 发送消息
        websocket.send_json({
            "type": "message",
            "content": "Hello"
        })

        # 接收错误响应（功能尚未实现）
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "not yet implemented" in data["message"]


# Note: Agent WebSocket connection tests would require creating a test agent
# with a valid API key in the database, which is more complex and would be
# better suited for end-to-end tests rather than integration tests.
# For now, we focus on the User authentication flow.
