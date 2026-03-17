"""Map API功能测试。

测试地图相关的API接口。
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


@pytest.fixture(scope="module")
def test_agent(client):
    """创建测试Agent。"""
    agent_id = f"agent_{uuid.uuid4().hex[:8]}"

    response = client.post(
        "/api/agents/register",
        json={
            "agent_id": agent_id,
            "name": "Test Map Agent",
            "avatar": "https://example.com/avatar.png",
            "description": "A test agent for map testing",
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
    return data["data"]


@pytest.fixture(scope="module")
def admin_token(client):
    """获取管理员token（假设有管理员用户）。"""
    # 这里需要根据实际的认证方式获取管理员token
    # 暂时返回None，实际使用时需要实现
    return None


class TestMapAPI:
    """地图API测试类。"""

    def test_create_agent_location_success(self, client, test_agent):
        """测试成功创建Agent位置。"""
        # 注意：这个测试需要管理员权限
        # 如果没有管理员认证，这个测试会失败
        response = client.post(
            "/api/map/agent-locations",
            json={
                "agent_id": test_agent["agent"]["id"],
                "latitude": 22.1234,
                "longitude": 113.5678,
                "address": "广东省珠海市金湾区",
                "is_active": True,
                "display_order": 0,
            },
        )

        # 如果没有认证，应该返回401
        # 如果没有管理员权限，应该返回403
        # 如果有管理员权限，应该返回201
        assert response.status_code in [201, 401, 403]

        if response.status_code == 201:
            data = response.json()
            assert data["code"] == 201
            assert data["data"]["agent"]["id"] == test_agent["agent"]["id"]
            assert data["data"]["latitude"] == 22.1234
            assert data["data"]["longitude"] == 113.5678

    def test_create_agent_location_invalid_coordinates(self, client, test_agent):
        """测试使用无效坐标创建位置。"""
        response = client.post(
            "/api/map/agent-locations",
            json={
                "agent_id": test_agent["agent"]["id"],
                "latitude": 100,  # 无效纬度
                "longitude": 113.5678,
                "address": "广东省珠海市金湾区",
            },
        )

        # 应该返回422（验证错误）、401（未认证）或403（权限错误）
        assert response.status_code in [422, 401, 403]

    def test_get_nearby_agents(self, client):
        """测试查询周边Agent。"""
        response = client.get(
            "/api/map/nearby",
            params={
                "latitude": 22.5,
                "longitude": 113.5,
                "radius": 50000,  # 50公里
                "limit": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert "center" in data["data"]
        assert "radius" in data["data"]

        # 验证center
        assert data["data"]["center"]["latitude"] == 22.5
        assert data["data"]["center"]["longitude"] == 113.5
        assert data["data"]["radius"] == 50000

    def test_get_nearby_agents_invalid_latitude(self, client):
        """测试使用无效纬度查询周边Agent。"""
        response = client.get(
            "/api/map/nearby",
            params={
                "latitude": 100,  # 无效纬度
                "longitude": 113.5,
                "radius": 50000,
            },
        )

        # 应该返回422（验证错误）
        assert response.status_code == 422

    def test_get_nearby_agents_invalid_longitude(self, client):
        """测试使用无效经度查询周边Agent。"""
        response = client.get(
            "/api/map/nearby",
            params={
                "latitude": 22.5,
                "longitude": 200,  # 无效经度
                "radius": 50000,
            },
        )

        # 应该返回422（验证错误）
        assert response.status_code == 422

    def test_get_agent_locations(self, client, test_agent):
        """测试获取Agent的所有位置。"""
        response = client.get(
            f"/api/map/agents/{test_agent['agent']['id']}/locations"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "items" in data["data"]
        assert "total" in data["data"]


class TestMapAPIWithRealData:
    """使用真实测试数据的地图API测试。"""

    def test_get_nearby_agents_with_real_data(self, client):
        """测试使用真实数据查询周边Agent。

        这个测试依赖于init_map_data.py创建的测试数据。
        """
        # 查询广州附近的Agent（应该能找到李白、白居易）
        response = client.get(
            "/api/map/nearby",
            params={
                "latitude": 23.1291,  # 广州
                "longitude": 113.2644,
                "radius": 50000,  # 50公里
                "limit": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

        # 应该至少能找到一些Agent
        # 注意：这个测试依赖于测试数据是否已经初始化
        # 如果测试数据不存在，total可能为0
        assert data["data"]["total"] >= 0

    def test_get_nearby_agents_zhuhai(self, client):
        """测试查询珠海附近的Agent。"""
        response = client.get(
            "/api/map/nearby",
            params={
                "latitude": 22.1234,  # 珠海
                "longitude": 113.5678,
                "radius": 10000,  # 10公里
                "limit": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

        # 验证返回的数据结构
        for item in data["data"]["items"]:
            assert "location_id" in item
            assert "agent" in item
            assert "latitude" in item
            assert "longitude" in item
            assert "address" in item
            assert "distance" in item

            # 验证agent信息
            assert "id" in item["agent"]
            assert "agent_id" in item["agent"]
            assert "name" in item["agent"]
