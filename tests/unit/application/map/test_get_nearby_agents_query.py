"""Test GetNearbyAgentsQuery."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock

from src.application.map.queries.get_nearby_agents_query import (
    GetNearbyAgentsQuery,
    GetNearbyAgentsQueryHandler,
)
from src.domain.map.entities.agent_location import AgentLocation
from src.domain.agent.entities.agent import Agent
from src.domain.agent.value_objects.agent_id import AgentId
from src.domain.agent.value_objects.api_key import ApiKey


@pytest.mark.asyncio
async def test_get_nearby_agents_success():
    """测试成功查询周边Agent。"""
    # Mock repository
    location_repo = AsyncMock()

    # 创建测试数据
    agent1_id = uuid4()
    agent2_id = uuid4()

    agent1 = Agent.create(
        agent_id=AgentId("agent_test1"),
        name="Test Agent 1",
        api_key=ApiKey.generate(),
    )
    agent1.id = agent1_id

    agent2 = Agent.create(
        agent_id=AgentId("agent_test2"),
        name="Test Agent 2",
        api_key=ApiKey.generate(),
    )
    agent2.id = agent2_id

    location1 = AgentLocation.create(
        agent_id=agent1_id,
        latitude=22.1234,
        longitude=113.5678,
        address="广东省珠海市金湾区"
    )

    location2 = AgentLocation.create(
        agent_id=agent2_id,
        latitude=22.2234,
        longitude=113.6678,
        address="广东省珠海市香洲区"
    )

    # Mock find_nearby_with_agents返回测试数据
    location_repo.find_nearby_with_agents.return_value = [
        (location1, agent1, 1000.0),
        (location2, agent2, 2000.0),
    ]

    # 创建Handler
    handler = GetNearbyAgentsQueryHandler(location_repo)

    # 创建查询
    query = GetNearbyAgentsQuery(
        latitude=22.1234,
        longitude=113.5678,
        radius=5000,
        limit=10
    )

    # 执行查询
    result = await handler.handle(query)

    # 验证结果
    assert result.total == 2
    assert len(result.items) == 2
    assert result.center["latitude"] == 22.1234
    assert result.center["longitude"] == 113.5678
    assert result.radius == 5000

    # 验证第一个结果
    assert result.items[0].agent.name == "Test Agent 1"
    assert result.items[0].distance == 1000.0

    # 验证第二个结果
    assert result.items[1].agent.name == "Test Agent 2"
    assert result.items[1].distance == 2000.0

    # 验证调用
    location_repo.find_nearby_with_agents.assert_called_once_with(
        latitude=22.1234,
        longitude=113.5678,
        radius=5000,
        limit=10,
        only_active=True
    )


@pytest.mark.asyncio
async def test_get_nearby_agents_empty_result():
    """测试查询周边Agent返回空结果。"""
    # Mock repository
    location_repo = AsyncMock()

    # Mock find_nearby_with_agents返回空列表
    location_repo.find_nearby_with_agents.return_value = []

    # 创建Handler
    handler = GetNearbyAgentsQueryHandler(location_repo)

    # 创建查询
    query = GetNearbyAgentsQuery(
        latitude=22.1234,
        longitude=113.5678,
        radius=5000,
        limit=10
    )

    # 执行查询
    result = await handler.handle(query)

    # 验证结果
    assert result.total == 0
    assert len(result.items) == 0
