"""Message entity unit tests."""
import pytest
from uuid import uuid4

from src.domain.messaging.entities.message import Message
from src.domain.messaging.enums.message_type import MessageType
from src.domain.messaging.value_objects.conversation_id import ConversationId
from src.domain.shared.value_objects.actor import Actor


class TestMessage:
    """Message实体测试。"""

    def test_create_text_message(self):
        """测试创建文本消息。"""
        conversation_id = ConversationId.generate()
        sender = Actor.from_user(uuid4())

        message = Message.create(
            conversation_id=conversation_id,
            sender=sender,
            content="Hello, world!"
        )

        assert message.conversation_id == conversation_id
        assert message.sender == sender
        assert message.content == "Hello, world!"
        assert message.message_type == MessageType.TEXT
        assert message.metadata is None

    def test_create_message_with_metadata(self):
        """测试创建带元数据的消息。"""
        conversation_id = ConversationId.generate()
        sender = Actor.from_agent(uuid4())
        metadata = {"key": "value", "number": 42}

        message = Message.create(
            conversation_id=conversation_id,
            sender=sender,
            content="Message with metadata",
            metadata=metadata
        )

        assert message.metadata == metadata

    def test_create_image_message(self):
        """测试创建图片消息。"""
        conversation_id = ConversationId.generate()
        sender = Actor.from_user(uuid4())

        message = Message.create(
            conversation_id=conversation_id,
            sender=sender,
            content="https://example.com/image.jpg",
            message_type=MessageType.IMAGE
        )

        assert message.message_type == MessageType.IMAGE

    def test_is_from(self):
        """测试判断消息来源。"""
        conversation_id = ConversationId.generate()
        sender = Actor.from_user(uuid4())
        other_actor = Actor.from_user(uuid4())

        message = Message.create(
            conversation_id=conversation_id,
            sender=sender,
            content="Test message"
        )

        assert message.is_from(sender)
        assert not message.is_from(other_actor)

    def test_user_sends_message(self):
        """测试User发送消息。"""
        conversation_id = ConversationId.generate()
        user = Actor.from_user(uuid4())

        message = Message.create(
            conversation_id=conversation_id,
            sender=user,
            content="Hello from user"
        )

        assert message.sender.is_user()
        assert message.is_from(user)

    def test_agent_sends_message(self):
        """测试Agent发送消息。"""
        conversation_id = ConversationId.generate()
        agent = Actor.from_agent(uuid4())

        message = Message.create(
            conversation_id=conversation_id,
            sender=agent,
            content="Hello from agent"
        )

        assert message.sender.is_agent()
        assert message.is_from(agent)

    def test_system_message(self):
        """测试系统消息。"""
        conversation_id = ConversationId.generate()
        system = Actor.from_user(uuid4())  # 系统也可以用User表示

        message = Message.create(
            conversation_id=conversation_id,
            sender=system,
            content="User joined the conversation",
            message_type=MessageType.SYSTEM
        )

        assert message.message_type == MessageType.SYSTEM
