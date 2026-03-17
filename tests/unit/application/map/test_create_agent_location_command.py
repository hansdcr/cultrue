"""Test CreateAgentLocationCommand."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from src.application.map.commands.create_agent_location_command import (
    CreateAgentLocationCommand,
    CreateAgentLocationCommandHandler,
)
from src.domain.map.entities.agent_location import AgentLocation
from src.domain.agent.entities.agent import Agent
from src.domain.agent.value_objects.agent_id import AgentId
from src.domain.agent.value_objects.api_key import ApiKey


@pytest.mark.asyncio
async def test_create_agent_location_success():
    """测试成功创建Agent位置。"""
    # Mock repositories
    location_repo = AsyncMock()
    agent_repo = AsyncMock()

    # 创建测试Agent
    agent_id_value = uuid4()
    test_agent = Agent.create(
        agent_id=AgentId("agent_test"),
        name="Test Agent",
        api_key=ApiKey.generate(),
    )
    test_agent.id = agent_id_value

    # Mock agent_repo.find_by_id返回测试Agent
    agent_repo.find_by_id.return_value = test_agent

    # Mock location_repo.save返回创建的位置
    def mock_save(location):
        return location

    location_repo.save.side_effect = mock_save

    # 创建Handler
    handler = CreateAgentLocationCommandHandler(location_repo, agent_repo)

    # 创建命令
    command = CreateAgentLocationCommand(
        agent_id=agent_id_value,
        latitude=22.1234,
        longitude=113.5678,
        address="广东省珠海市金湾区"
    )

    # 执行命令
    result = await handler.handle(command)

    # 验证结果
    assert result.location_id is not None
    assert result.agent.id == str(agent_id_value)
    assert result.latitude == 22.1234
    assert result.longitude == 113.5678
    assert result.address == "广东省珠海市金湾区"

    # 验证调用
    agent_repo.find_by_id.assert_called_once_with(agent_id_value)
    location_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_create_agent_location_agent_not_found():
    """测试Agent不存在时创建位置失败。"""
    # Mock repositories
    location_repo = AsyncMock()
    agent_repo = AsyncMock()

    # Mock agent_repo.find_by_id返回None
    agent_repo.find_by_id.return_value = None

    # 创建Handler
    handler = CreateAgentLocationCommandHandler(location_repo, agent_repo)

    # 创建命令
    command = CreateAgentLocationCommand(
        agent_id=uuid4(),
        latitude=22.1234,
        longitude=113.5678,
        address="广东省珠海市金湾区"
    )

    # 执行命令应该抛出异常
    with pytest.raises(ValueError, match="Agent with ID .* not found"):
        await handler.handle(command)


@pytest.mark.asyncio
async def test_create_agent_location_invalid_coordinates():
    """测试无效坐标创建位置失败。"""
    # Mock repositories
    location_repo = AsyncMock()
    agent_repo = AsyncMock()

    # 创建Handler
    handler = CreateAgentLocationCommandHandler(location_repo, agent_repo)

    # 创建命令（无效纬度）
    command = CreateAgentLocationCommand(
        agent_id=uuid4(),
        latitude=100,  # 无效纬度
        longitude=113.5678,
        address="广东省珠海市金湾区"
    )

    # 执行命令应该抛出异常
    with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
        await handler.handle(command)
