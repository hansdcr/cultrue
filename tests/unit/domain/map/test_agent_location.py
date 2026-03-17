"""Test AgentLocation entity."""
import pytest
from uuid import uuid4

from src.domain.map.entities.agent_location import AgentLocation


def test_create_agent_location():
    """测试创建Agent位置。"""
    agent_id = uuid4()

    location = AgentLocation.create(
        agent_id=agent_id,
        latitude=22.1234,
        longitude=113.5678,
        address="广东省珠海市金湾区"
    )

    assert location.agent_id == agent_id
    assert location.latitude == 22.1234
    assert location.longitude == 113.5678
    assert location.address == "广东省珠海市金湾区"
    assert location.is_active is True
    assert location.display_order == 0
    assert location.metadata == {}


def test_create_agent_location_with_metadata():
    """测试创建带元数据的Agent位置。"""
    agent_id = uuid4()
    metadata = {"tags": ["景点", "历史"], "rating": 4.5}

    location = AgentLocation.create(
        agent_id=agent_id,
        latitude=22.1234,
        longitude=113.5678,
        address="广东省珠海市金湾区",
        metadata=metadata
    )

    assert location.metadata == metadata


def test_invalid_latitude():
    """测试无效的纬度。"""
    agent_id = uuid4()

    with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
        AgentLocation.create(
            agent_id=agent_id,
            latitude=100,  # 无效纬度
            longitude=113.5678,
            address="广东省珠海市金湾区"
        )


def test_invalid_longitude():
    """测试无效的经度。"""
    agent_id = uuid4()

    with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
        AgentLocation.create(
            agent_id=agent_id,
            latitude=22.1234,
            longitude=200,  # 无效经度
            address="广东省珠海市金湾区"
        )


def test_distance_calculation():
    """测试距离计算。"""
    agent_id = uuid4()

    # 珠海某地
    location = AgentLocation.create(
        agent_id=agent_id,
        latitude=22.1234,
        longitude=113.5678,
        address="广东省珠海市金湾区"
    )

    # 计算到附近某点的距离
    distance = location.distance_to(22.2234, 113.6678)

    # 距离应该大于0且小于20公里
    assert distance > 0
    assert distance < 20000


def test_activate_deactivate():
    """测试激活和停用位置。"""
    agent_id = uuid4()

    location = AgentLocation.create(
        agent_id=agent_id,
        latitude=22.1234,
        longitude=113.5678,
        address="广东省珠海市金湾区"
    )

    assert location.is_active is True

    # 停用
    location.deactivate()
    assert location.is_active is False

    # 激活
    location.activate()
    assert location.is_active is True


def test_update_location():
    """测试更新位置信息。"""
    agent_id = uuid4()

    location = AgentLocation.create(
        agent_id=agent_id,
        latitude=22.1234,
        longitude=113.5678,
        address="广东省珠海市金湾区"
    )

    # 更新位置
    location.update_location(
        latitude=23.1291,
        longitude=113.2644,
        address="广东省广州市天河区"
    )

    assert location.latitude == 23.1291
    assert location.longitude == 113.2644
    assert location.address == "广东省广州市天河区"


def test_update_location_with_invalid_coordinates():
    """测试使用无效坐标更新位置。"""
    agent_id = uuid4()

    location = AgentLocation.create(
        agent_id=agent_id,
        latitude=22.1234,
        longitude=113.5678,
        address="广东省珠海市金湾区"
    )

    with pytest.raises(ValueError):
        location.update_location(
            latitude=100,  # 无效纬度
            longitude=113.2644,
            address="广东省广州市天河区"
        )
