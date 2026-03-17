"""Conversation API集成测试。

测试会话管理API接口。
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


@pytest.fixture
def test_user_token(client):
    """创建测试用户并获取token。

    注意: 这需要先实现用户注册和登录API。
    """
    # TODO: 实现用户注册和登录
    # 暂时返回一个模拟token
    return "test_token"


@pytest.fixture
def test_agent_api_key(client):
    """创建测试Agent并获取API Key。"""
    agent_id = f"agent_{uuid.uuid4().hex[:8]}"

    response = client.post(
        "/api/agents/register",
        json={
            "agent_id": agent_id,
            "name": "Test Agent for Conversation",
        },
    )

    assert response.status_code == 201
    return response.json()["data"]["api_key"]


class TestConversationCreationAPI:
    """会话创建API测试类。"""

    def test_create_direct_conversation_user_agent(self, client, test_agent_api_key):
        """测试创建User与Agent的一对一会话。

        注意: 这个测试需要有效的用户认证token。
        目前跳过,等待用户认证系统完善。
        """
        pytest.skip("需要用户认证系统")

    def test_create_group_conversation(self, client):
        """测试创建群聊。

        注意: 这个测试需要有效的用户认证token。
        目前跳过,等待用户认证系统完善。
        """
        pytest.skip("需要用户认证系统")

    def test_create_conversation_without_auth(self, client):
        """测试未认证时创建会话应该失败。"""
        response = client.post(
            "/api/conversations",
            json={
                "conversation_type": "direct",
                "members": [
                    {"actor_type": "user", "actor_id": str(uuid.uuid4())},
                    {"actor_type": "agent", "actor_id": str(uuid.uuid4())},
                ],
            },
        )

        # 应该返回401未认证
        assert response.status_code == 401


class TestConversationListAPI:
    """会话列表API测试类。"""

    def test_list_conversations_without_auth(self, client):
        """测试未认证时获取会话列表应该失败。"""
        response = client.get("/api/conversations")

        # 应该返回401未认证
        assert response.status_code == 401


class TestConversationDetailAPI:
    """会话详情API测试类。"""

    def test_get_conversation_without_auth(self, client):
        """测试未认证时获取会话详情应该失败。"""
        conversation_id = uuid.uuid4()
        response = client.get(f"/api/conversations/{conversation_id}")

        # 应该返回401未认证
        assert response.status_code == 401


# 注意: 完整的集成测试需要:
# 1. 用户注册和登录API
# 2. 数据库fixture设置
# 3. 测试数据清理
# 4. 更多的边界情况测试
#
# 这些将在用户认证系统完善后添加。
