"""Test Actor value object."""
import pytest
from uuid import uuid4

from src.domain.shared.value_objects.actor import Actor
from src.domain.shared.enums.actor_type import ActorType


def test_create_actor_from_user():
    """测试从User创建Actor。"""
    user_id = uuid4()
    actor = Actor.from_user(user_id)

    assert actor.actor_type == ActorType.USER
    assert actor.actor_id == user_id
    assert actor.is_user()
    assert not actor.is_agent()


def test_create_actor_from_agent():
    """测试从Agent创建Actor。"""
    agent_id = uuid4()
    actor = Actor.from_agent(agent_id)

    assert actor.actor_type == ActorType.AGENT
    assert actor.actor_id == agent_id
    assert actor.is_agent()
    assert not actor.is_user()


def test_actor_equality():
    """测试Actor相等性。"""
    user_id = uuid4()
    actor1 = Actor.from_user(user_id)
    actor2 = Actor.from_user(user_id)

    assert actor1 == actor2


def test_actor_immutability():
    """测试Actor不可变性。"""
    user_id = uuid4()
    actor = Actor.from_user(user_id)

    with pytest.raises(Exception):  # dataclass frozen=True会抛出异常
        actor.actor_id = uuid4()
