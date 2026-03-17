"""Message API集成测试。

测试消息管理API接口。
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    """创建测试客户端。"""
    with TestClient(app) as test_client:
        yield test_client


class TestMessageSendAPI:
    """消息发送API测试类。"""

    def test_send_message_without_auth(self, client):
        """测试未认证时发送消息应该失败。"""
        conversation_id = uuid.uuid4()
        response = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={
                "message_type": "text",
                "content": "Hello!",
            },
        )

        # 应该返回401未认证
        assert response.status_code == 401


class TestMessageListAPI:
    """消息列表API测试类。"""

    def test_list_messages_without_auth(self, client):
        """测试未认证时获取消息列表应该失败。"""
        conversation_id = uuid.uuid4()
        response = client.get(f"/api/conversations/{conversation_id}/messages")

        # 应该返回401未认证
        assert response.status_code == 401


class TestMessageDetailAPI:
    """消息详情API测试类。"""

    def test_get_message_without_auth(self, client):
        """测试未认证时获取消息详情应该失败。"""
        message_id = uuid.uuid4()
        response = client.get(f"/api/messages/{message_id}")

        # 应该返回401未认证
        assert response.status_code == 401


class TestMessageDeleteAPI:
    """消息删除API测试类。"""

    def test_delete_message_without_auth(self, client):
        """测试未认证时删除消息应该失败。"""
        message_id = uuid.uuid4()
        response = client.delete(f"/api/messages/{message_id}")

        # 应该返回401未认证
        assert response.status_code == 401


# 注意: 完整的集成测试需要:
# 1. 用户注册和登录API
# 2. 创建测试会话
# 3. 测试发送消息
# 4. 测试查询消息
# 5. 测试删除消息
# 6. 测试权限控制
#
# 这些将在用户认证系统完善后添加。
