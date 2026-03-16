"""Agent API接口功能测试。

测试Agent注册、认证、管理等API接口。
使用真实数据库进行测试，测试前后清理数据。
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


def generate_unique_agent_id():
    """生成唯一的Agent ID。"""
    return f"agent_{uuid.uuid4().hex[:8]}"


class TestAgentRegistrationAPI:
    """Agent注册API测试类。"""

    def test_register_agent_success(self, client):
        """测试Agent注册成功。"""
        agent_id = generate_unique_agent_id()

        response = client.post(
            "/api/agents/register",
            json={
                "agent_id": agent_id,
                "name": "Test Agent",
                "avatar": "https://example.com/avatar.png",
                "description": "A test agent",
                "system_prompt": "You are a helpful assistant",
                "agent_model_config": {
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "model": "claude-sonnet-4",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 201
        assert data["data"]["agent"]["agent_id"] == agent_id
        assert data["data"]["agent"]["name"] == "Test Agent"
        assert "api_key" in data["data"]
        assert data["data"]["api_key"].startswith("ak_")
        assert data["message"] == "Agent registered successfully"

    def test_register_agent_minimal_fields(self, client):
        """测试使用最少必填字段注册Agent。"""
        agent_id = generate_unique_agent_id()

        response = client.post(
            "/api/agents/register",
            json={
                "agent_id": agent_id,
                "name": "Minimal Agent",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["agent"]["agent_id"] == agent_id
        assert data["data"]["agent"]["name"] == "Minimal Agent"
        assert "api_key" in data["data"]


class TestAgentAuthenticationAPI:
    """Agent认证API测试类。"""

    def test_get_agent_with_api_key_success(self, client):
        """测试使用API Key认证获取Agent信息成功。"""
        # 注册Agent
        agent_id = generate_unique_agent_id()
        register_response = client.post(
            "/api/agents/register",
            json={
                "agent_id": agent_id,
                "name": "Auth Test Agent",
                "description": "Testing authentication",
            },
        )
        api_key = register_response.json()["data"]["api_key"]
        agent_uuid = register_response.json()["data"]["agent"]["id"]

        # 使用API Key获取Agent信息
        response = client.get(
            f"/api/agents/{agent_uuid}",
            headers={"Authorization": f"Bearer {api_key}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["agent_id"] == agent_id
        assert data["data"]["name"] == "Auth Test Agent"


class TestAgentManagementAPI:
    """Agent管理API测试类。"""

    def test_list_agents_success(self, client):
        """测试获取Agent列表成功。"""
        # 注册几个Agent
        for i in range(3):
            agent_id = generate_unique_agent_id()
            client.post(
                "/api/agents/register",
                json={
                    "agent_id": agent_id,
                    "name": f"List Test Agent {i}",
                },
            )

        # 获取Agent列表
        response = client.get("/api/agents")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert data["data"]["total"] >= 3

    def test_list_agents_with_pagination(self, client):
        """测试Agent列表分页。"""
        response = client.get("/api/agents?limit=5&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["limit"] == 5
        assert data["data"]["offset"] == 0
        assert len(data["data"]["items"]) <= 5

    def test_list_agents_filter_by_active(self, client):
        """测试按活跃状态过滤Agent列表。"""
        response = client.get("/api/agents?is_active=true")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        # 所有返回的Agent应该是活跃的
        for agent in data["data"]["items"]:
            assert agent["is_active"] is True

    def test_get_agent_by_id_success(self, client):
        """测试通过ID获取Agent详情成功。"""
        # 注册Agent
        agent_id = generate_unique_agent_id()
        register_response = client.post(
            "/api/agents/register",
            json={
                "agent_id": agent_id,
                "name": "Get By ID Agent",
                "description": "Testing get by ID",
            },
        )
        api_key = register_response.json()["data"]["api_key"]
        agent_uuid = register_response.json()["data"]["agent"]["id"]

        # 获取Agent详情
        response = client.get(
            f"/api/agents/{agent_uuid}",
            headers={"Authorization": f"Bearer {api_key}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == agent_uuid
        assert data["data"]["agent_id"] == agent_id
        assert data["data"]["name"] == "Get By ID Agent"

    def test_update_agent_success(self, client):
        """测试更新Agent信息成功。"""
        # 注册Agent
        agent_id = generate_unique_agent_id()
        register_response = client.post(
            "/api/agents/register",
            json={
                "agent_id": agent_id,
                "name": "Original Name",
                "description": "Original description",
            },
        )
        api_key = register_response.json()["data"]["api_key"]
        agent_uuid = register_response.json()["data"]["agent"]["id"]

        # 更新Agent信息
        response = client.put(
            f"/api/agents/{agent_uuid}",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "name": "Updated Name",
                "description": "Updated description",
                "system_prompt": "New system prompt",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["name"] == "Updated Name"
        assert data["data"]["description"] == "Updated description"
        assert data["data"]["system_prompt"] == "New system prompt"

    def test_update_agent_partial_fields(self, client):
        """测试部分更新Agent信息。"""
        # 注册Agent
        agent_id = generate_unique_agent_id()
        register_response = client.post(
            "/api/agents/register",
            json={
                "agent_id": agent_id,
                "name": "Original Name",
                "description": "Original description",
            },
        )
        api_key = register_response.json()["data"]["api_key"]
        agent_uuid = register_response.json()["data"]["agent"]["id"]

        # 只更新name字段
        response = client.put(
            f"/api/agents/{agent_uuid}",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "name": "Only Name Updated",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Only Name Updated"
        assert data["data"]["description"] == "Original description"


class TestCompleteAgentFlow:
    """完整Agent流程测试类。"""

    def test_complete_agent_flow(self, client):
        """测试完整的Agent流程：注册 -> 认证 -> 获取信息 -> 更新。"""
        # 1. 注册Agent
        agent_id = generate_unique_agent_id()
        register_response = client.post(
            "/api/agents/register",
            json={
                "agent_id": agent_id,
                "name": "Flow Test Agent",
                "description": "Testing complete flow",
                "system_prompt": "You are a test agent",
                "agent_model_config": {
                    "temperature": 0.8,
                    "max_tokens": 1500,
                    "model": "claude-sonnet-4",
                },
            },
        )
        assert register_response.status_code == 201
        api_key = register_response.json()["data"]["api_key"]
        agent_uuid = register_response.json()["data"]["agent"]["id"]
        assert api_key.startswith("ak_")

        # 2. 使用API Key获取Agent信息
        get_response = client.get(
            f"/api/agents/{agent_uuid}",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert get_response.status_code == 200
        assert get_response.json()["data"]["agent_id"] == agent_id

        # 3. 获取Agent列表，验证新Agent在列表中
        list_response = client.get("/api/agents")
        assert list_response.status_code == 200
        agent_ids = [agent["agent_id"] for agent in list_response.json()["data"]["items"]]
        assert agent_id in agent_ids

        # 4. 更新Agent信息
        update_response = client.put(
            f"/api/agents/{agent_uuid}",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "name": "Flow Test Agent Updated",
                "description": "Updated description",
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["name"] == "Flow Test Agent Updated"
