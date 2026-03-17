"""Conversation entity unit tests."""
import pytest
from uuid import uuid4

from src.domain.messaging.entities.conversation import Conversation
from src.domain.messaging.enums.conversation_status import ConversationStatus
from src.domain.messaging.enums.conversation_type import ConversationType
from src.domain.shared.value_objects.actor import Actor


class TestConversation:
    """Conversation实体测试。"""

    def test_create_direct_conversation(self):
        """测试创建一对一会话。"""
        user1 = Actor.from_user(uuid4())
        user2 = Actor.from_user(uuid4())

        conversation = Conversation.create_direct(user1, user2)

        assert conversation.is_direct()
        assert not conversation.is_group()
        assert conversation.status == ConversationStatus.ACTIVE
        assert len(conversation.members) == 2
        assert conversation.has_member(user1)
        assert conversation.has_member(user2)
        assert conversation.message_count == 0
        assert conversation.title is None

    def test_create_group_conversation(self):
        """测试创建群聊。"""
        user = Actor.from_user(uuid4())
        agent1 = Actor.from_agent(uuid4())
        agent2 = Actor.from_agent(uuid4())

        conversation = Conversation.create_group(
            "Study Group",
            [user, agent1, agent2]
        )

        assert conversation.is_group()
        assert not conversation.is_direct()
        assert conversation.status == ConversationStatus.ACTIVE
        assert conversation.title == "Study Group"
        assert len(conversation.members) == 3
        assert conversation.has_member(user)
        assert conversation.has_member(agent1)
        assert conversation.has_member(agent2)

    def test_add_member(self):
        """测试添加成员。"""
        user1 = Actor.from_user(uuid4())
        user2 = Actor.from_user(uuid4())
        user3 = Actor.from_user(uuid4())

        conversation = Conversation.create_direct(user1, user2)
        conversation.add_member(user3)

        assert len(conversation.members) == 3
        assert conversation.has_member(user3)

    def test_add_duplicate_member(self):
        """测试添加重复成员（应该被忽略）。"""
        user1 = Actor.from_user(uuid4())
        user2 = Actor.from_user(uuid4())

        conversation = Conversation.create_direct(user1, user2)
        conversation.add_member(user1)  # 重复添加

        assert len(conversation.members) == 2  # 数量不变

    def test_remove_member(self):
        """测试移除成员。"""
        user1 = Actor.from_user(uuid4())
        user2 = Actor.from_user(uuid4())

        conversation = Conversation.create_direct(user1, user2)
        conversation.remove_member(user2)

        assert len(conversation.members) == 1
        assert not conversation.has_member(user2)
        assert conversation.has_member(user1)

    def test_user_to_user_conversation(self):
        """测试User ↔ User会话。"""
        user1 = Actor.from_user(uuid4())
        user2 = Actor.from_user(uuid4())

        conversation = Conversation.create_direct(user1, user2)

        assert conversation.is_direct()
        assert all(member.is_user() for member in conversation.members)

    def test_user_to_agent_conversation(self):
        """测试User ↔ Agent会话。"""
        user = Actor.from_user(uuid4())
        agent = Actor.from_agent(uuid4())

        conversation = Conversation.create_direct(user, agent)

        assert conversation.is_direct()
        assert conversation.has_member(user)
        assert conversation.has_member(agent)

    def test_agent_to_agent_conversation(self):
        """测试Agent ↔ Agent会话。"""
        agent1 = Actor.from_agent(uuid4())
        agent2 = Actor.from_agent(uuid4())

        conversation = Conversation.create_direct(agent1, agent2)

        assert conversation.is_direct()
        assert all(member.is_agent() for member in conversation.members)
