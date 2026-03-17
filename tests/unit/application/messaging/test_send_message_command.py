"""Test SendMessageCommand."""
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.application.messaging.commands.send_message_command import (
    SendMessageCommand,
    SendMessageCommandHandler,
)
from src.domain.messaging.entities.conversation import Conversation
from src.domain.messaging.entities.message import Message
from src.domain.messaging.enums.message_type import MessageType
from src.domain.messaging.value_objects.conversation_id import ConversationId
from src.domain.messaging.value_objects.message_id import MessageId
from src.domain.shared.value_objects.actor import Actor
from src.domain.shared.exceptions import DomainException, NotFoundException


@pytest.mark.asyncio
async def test_send_message_success():
    """测试成功发送消息。"""
    # Arrange
    user1_id = uuid4()
    user2_id = uuid4()
    actor1 = Actor.from_user(user1_id)
    actor2 = Actor.from_user(user2_id)

    conversation = Conversation.create_direct(actor1, actor2)
    conversation_id = conversation.id.value

    # Mock repositories
    mock_conversation_repo = AsyncMock()
    mock_conversation_repo.find_by_id.return_value = conversation

    mock_message_repo = AsyncMock()
    message = Message.create(
        conversation_id=conversation.id,
        sender=actor1,
        content="Hello!",
        message_type=MessageType.TEXT,
    )
    mock_message_repo.save.return_value = message

    # Create handler
    handler = SendMessageCommandHandler(
        mock_message_repo, mock_conversation_repo
    )

    # Create command
    command = SendMessageCommand(
        conversation_id=conversation_id,
        sender=actor1,
        message_type="text",
        content="Hello!",
    )

    # Act
    result = await handler.handle(command)

    # Assert
    assert result.content == "Hello!"
    assert result.message_type == "text"
    assert result.sender.actor_type == "user"
    mock_conversation_repo.find_by_id.assert_called_once()
    mock_message_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_send_message_conversation_not_found():
    """测试发送消息时会话不存在。"""
    # Arrange
    user_id = uuid4()
    actor = Actor.from_user(user_id)
    conversation_id = uuid4()

    # Mock repositories
    mock_conversation_repo = AsyncMock()
    mock_conversation_repo.find_by_id.return_value = None  # 会话不存在

    mock_message_repo = AsyncMock()

    # Create handler
    handler = SendMessageCommandHandler(
        mock_message_repo, mock_conversation_repo
    )

    # Create command
    command = SendMessageCommand(
        conversation_id=conversation_id,
        sender=actor,
        message_type="text",
        content="Hello!",
    )

    # Act & Assert
    with pytest.raises(NotFoundException, match="Conversation not found"):
        await handler.handle(command)


@pytest.mark.asyncio
async def test_send_message_sender_not_member():
    """测试发送消息时发送者不是会话成员。"""
    # Arrange
    user1_id = uuid4()
    user2_id = uuid4()
    user3_id = uuid4()
    actor1 = Actor.from_user(user1_id)
    actor2 = Actor.from_user(user2_id)
    actor3 = Actor.from_user(user3_id)  # 不是会话成员

    conversation = Conversation.create_direct(actor1, actor2)
    conversation_id = conversation.id.value

    # Mock repositories
    mock_conversation_repo = AsyncMock()
    mock_conversation_repo.find_by_id.return_value = conversation

    mock_message_repo = AsyncMock()

    # Create handler
    handler = SendMessageCommandHandler(
        mock_message_repo, mock_conversation_repo
    )

    # Create command with non-member sender
    command = SendMessageCommand(
        conversation_id=conversation_id,
        sender=actor3,  # 不是会话成员
        message_type="text",
        content="Hello!",
    )

    # Act & Assert
    with pytest.raises(DomainException, match="not a member"):
        await handler.handle(command)
