"""WebSocket连接功能测试（迭代9）。

从用户使用角度测试WebSocket连接的完整流程。

注意：这些测试需要完整的应用环境，包括：
- 数据库连接
- WebSocket连接管理器初始化
- 事件总线初始化

运行这些测试前，请确保：
1. 数据库已启动并配置正确
2. 应用已完全初始化
3. 使用真实的测试环境而非mock

这些测试目前被标记为skip，因为TestClient不会触发lifespan事件。
要运行这些测试，需要：
1. 启动完整的应用服务器
2. 使用真实的WebSocket客户端连接
3. 或者修改测试以手动初始化所有依赖
"""
import asyncio
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from main import app
from src.infrastructure.security.jwt_service import jwt_service


@pytest.fixture
def client():
    """创建测试客户端。"""
    return TestClient(app)


@pytest.fixture
def user_id():
    """创建测试用户ID。"""
    return str(uuid4())


@pytest.fixture
def user_token(user_id):
    """创建User JWT token。"""
    return jwt_service.create_access_token(user_id)


class TestWebSocketConnection:
    """WebSocket连接功能测试。"""

    def test_user_can_connect_with_valid_token(self, client, user_token):
        """测试用户可以使用有效token连接WebSocket。

        场景：
        1. 用户使用有效的JWT token连接WebSocket
        2. 系统接受连接并返回连接成功消息
        3. 消息包含连接ID、actor信息和连接时间
        """
        with client.websocket_connect(f"/ws?token={user_token}") as websocket:
            # 接收连接成功消息
            data = websocket.receive_json()

            assert data["type"] == "connection_established"
            assert "connection_id" in data["data"]
            assert data["data"]["actor_type"] == "user"
            assert "actor_id" in data["data"]
            assert "connected_at" in data["data"]

    def test_user_cannot_connect_without_credentials(self, client):
        """测试用户无法在没有认证信息的情况下连接。

        场景：
        1. 用户尝试连接WebSocket但不提供token或api_key
        2. 系统拒绝连接（连接被关闭，code=4000）
        """
        from starlette.websockets import WebSocketDisconnect
        with client.websocket_connect("/ws") as ws:
            with pytest.raises((WebSocketDisconnect, Exception)):
                ws.receive_json()

    def test_user_cannot_connect_with_invalid_token(self, client):
        """测试用户无法使用无效token连接。

        场景：
        1. 用户使用无效的JWT token连接WebSocket
        2. 系统拒绝连接（连接被关闭，code=4001）
        """
        from starlette.websockets import WebSocketDisconnect
        with client.websocket_connect("/ws?token=invalid_token") as ws:
            with pytest.raises((WebSocketDisconnect, Exception)):
                ws.receive_json()

    def test_user_can_send_heartbeat(self, client, user_token):
        """测试用户可以发送心跳保持连接。

        场景：
        1. 用户连接WebSocket
        2. 用户发送ping消息
        3. 系统返回pong消息
        """
        with client.websocket_connect(f"/ws?token={user_token}") as websocket:
            # 接收连接成功消息
            websocket.receive_json()

            # 发送心跳
            websocket.send_json({"type": "ping"})

            # 接收心跳响应
            data = websocket.receive_json()
            assert data["type"] == "pong"
            assert "timestamp" in data

    def test_user_receives_error_for_unknown_message_type(self, client, user_token):
        """测试用户发送未知消息类型时收到错误。

        场景：
        1. 用户连接WebSocket
        2. 用户发送未知类型的消息
        3. 系统返回错误消息
        """
        with client.websocket_connect(f"/ws?token={user_token}") as websocket:
            # 接收连接成功消息
            websocket.receive_json()

            # 发送未知消息类型
            websocket.send_json({"type": "unknown_type"})

            # 接收错误响应
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "Unknown message type" in data["message"]

    def test_user_can_send_message_acknowledgement(self, client, user_token):
        """测试用户可以发送消息送达确认。

        场景：
        1. 用户连接WebSocket
        2. 用户发送消息送达确认（ack）
        3. 系统接受确认（不返回错误）
        """
        with client.websocket_connect(f"/ws?token={user_token}") as websocket:
            # 接收连接成功消息
            websocket.receive_json()

            # 发送消息确认
            message_id = str(uuid4())
            websocket.send_json({
                "type": "ack",
                "message_id": message_id
            })

            # 不应该收到错误消息
            # 如果有消息，应该是其他类型的推送，不是错误
            # 这里我们只是验证不会崩溃


class TestWebSocketMultiDevice:
    """WebSocket多设备连接测试。"""

    def test_user_can_connect_from_multiple_devices(self, client, user_token):
        """测试用户可以从多个设备同时连接。

        场景：
        1. 用户从第一个设备连接WebSocket
        2. 用户从第二个设备连接WebSocket
        3. 两个连接都成功建立
        """
        with client.websocket_connect(f"/ws?token={user_token}") as ws1:
            # 第一个设备连接成功
            data1 = ws1.receive_json()
            assert data1["type"] == "connection_established"

            with client.websocket_connect(f"/ws?token={user_token}") as ws2:
                # 第二个设备连接成功
                data2 = ws2.receive_json()
                assert data2["type"] == "connection_established"

                # 两个连接ID应该不同
                assert data1["data"]["connection_id"] != data2["data"]["connection_id"]

                # 但actor_id应该相同
                assert data1["data"]["actor_id"] == data2["data"]["actor_id"]
