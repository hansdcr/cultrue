"""Test Agent entity."""
import pytest
from uuid import uuid4

from src.domain.agent.entities.agent import Agent
from src.domain.agent.value_objects.agent_id import AgentId
from src.domain.agent.value_objects.api_key import ApiKey
from src.domain.agent.value_objects.agent_config import AgentConfig


def test_create_agent():
    """测试创建Agent。"""
    agent_id = AgentId("agent_test")
    api_key = ApiKey.generate()

    agent = Agent.create(
        agent_id=agent_id,
        name="Test Agent",
        api_key=api_key,
        description="A test agent",
    )

    assert agent.agent_id == agent_id
    assert agent.name == "Test Agent"
    assert agent.description == "A test agent"
    assert agent.is_active
    assert agent.verify_api_key(api_key)


def test_agent_verify_api_key():
    """测试验证API Key。"""
    agent_id = AgentId("agent_test")
    api_key = ApiKey.generate()

    agent = Agent.create(
        agent_id=agent_id,
        name="Test Agent",
        api_key=api_key,
    )

    # 正确的API Key
    assert agent.verify_api_key(api_key)

    # 错误的API Key
    wrong_api_key = ApiKey.generate()
    assert not agent.verify_api_key(wrong_api_key)


def test_agent_regenerate_api_key():
    """测试重新生成API Key。"""
    agent_id = AgentId("agent_test")
    old_api_key = ApiKey.generate()

    agent = Agent.create(
        agent_id=agent_id,
        name="Test Agent",
        api_key=old_api_key,
    )

    # 重新生成API Key
    new_api_key = agent.regenerate_api_key()

    # 旧的API Key应该失效
    assert not agent.verify_api_key(old_api_key)

    # 新的API Key应该有效
    assert agent.verify_api_key(new_api_key)


def test_agent_update_info():
    """测试更新Agent信息。"""
    agent_id = AgentId("agent_test")
    api_key = ApiKey.generate()

    agent = Agent.create(
        agent_id=agent_id,
        name="Test Agent",
        api_key=api_key,
    )

    # 更新信息
    new_config = AgentConfig(temperature=0.9, max_tokens=3000)
    agent.update_info(
        name="Updated Agent",
        description="Updated description",
        model_config=new_config,
    )

    assert agent.name == "Updated Agent"
    assert agent.description == "Updated description"
    assert agent.model_config.temperature == 0.9
    assert agent.model_config.max_tokens == 3000


def test_agent_activate_deactivate():
    """测试激活/停用Agent。"""
    agent_id = AgentId("agent_test")
    api_key = ApiKey.generate()

    agent = Agent.create(
        agent_id=agent_id,
        name="Test Agent",
        api_key=api_key,
    )

    assert agent.is_active

    # 停用
    agent.deactivate()
    assert not agent.is_active

    # 激活
    agent.activate()
    assert agent.is_active


def test_agent_to_actor():
    """测试转换为Actor。"""
    agent_id = AgentId("agent_test")
    api_key = ApiKey.generate()

    agent = Agent.create(
        agent_id=agent_id,
        name="Test Agent",
        api_key=api_key,
    )

    actor = agent.to_actor()
    assert actor.is_agent()
    assert actor.actor_id == agent.id
