"""Test CreateConversationCommand."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.application.messaging.commands.create_conversation_command import (
    CreateConversationCommand,
    CreateConversationCommandHandler,
)
from src.domain.messaging.entities.conversation import Conversation
from src.domain.messaging.enums.conversation_type import ConversationType
from src.domain.messaging.enums.conversation_status import ConversationStatus
from src.domain.messaging.value_objects.conversation_id import ConversationId
from src.domain.shared.value_objects.actor import Actor
from src.domain.shared.exceptions import DomainException


@pytest.mark.asyncio
async def test_create_direct_conversation():
    """测试创建一对一会话。"""
    # Arrange
    user1_id = uuid4()
    user2_id = uuid4()
    actor1 = Actor.from_user(user1_id)
    actor2 = Actor.from_user(user2_id)

    # Mock repository
    mock_repo = AsyncMock()
    mock_repo.find_direct_conversation.return_value = None  # 不存在已有会话

    # 创建一个模拟的会话对象
    conversation = Conversation.create_direct(actor1, actor2)
    mock_repo.save.return_value = conversation

    # Create handler
    handler = CreateConversationCommandHandler(mock_repo)

    # Create command
    command = CreateConversationCommand(
        conversation_type="direct",
        members=[actor1, actor2],
        creator=actor1,
    )

    # Act
    result = await handler.handle(command)

    # Assert
    assert result.conversation_type == "direct"
    assert len(result.members) == 2
    assert result.message_count == 0
    mock_repo.find_direct_conversation.assert_called_once_with(actor1, actor2)
    mock_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_create_direct_conversation_already_exists():
    """测试创建已存在的一对一会话。"""
    # Arrange
    user1_id = uuid4()
    user2_id = uuid4()
    actor1 = Actor.from_user(user1_id)
    actor2 = Actor.from_user(user2_id)

    # Mock repository
    mock_repo = AsyncMock()
    existing_conversation = Conversation.create_direct(actor1, actor2)
    mock_repo.find_direct_conversation.return_value = existing_conversation

    # Create handler
    handler = CreateConversationCommandHandler(mock_repo)

    # Create command
    command = CreateConversationCommand(
        conversation_type="direct",
        members=[actor1, actor2],
        creator=actor1,
    )

    # Act
    result = await handler.handle(command)

    # Assert
    assert result.id == str(existing_conversation.id.value)
    mock_repo.find_direct_conversation.assert_called_once_with(actor1, actor2)
    mock_repo.save.assert_not_called()  # 不应该保存新会话


@pytest.mark.asyncio
async def test_create_group_conversation():
    """测试创建群聊。"""
    # Arrange
    user1_id = uuid4()
    user2_id = uuid4()
    agent_id = uuid4()
    actor1 = Actor.from_user(user1_id)
    actor2 = Actor.from_user(user2_id)
    actor3 = Actor.from_agent(agent_id)

    # Mock repository
    mock_repo = AsyncMock()
    conversation = Conversation.create_group("Test Group", [actor1, actor2, actor3])
    mock_repo.save.return_value = conversation

    # Create handler
    handler = CreateConversationCommandHandler(mock_repo)

    # Create command
    command = CreateConversationCommand(
        conversation_type="group",
        members=[actor1, actor2, actor3],
        title="Test Group",
        creator=actor1,
    )

    # Act
    result = await handler.handle(command)

    # Assert
    assert result.conversation_type == "group"
    assert len(result.members) == 3
    assert result.title == "Test Group"
    mock_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_create_direct_conversation_invalid_member_count():
    """测试创建一对一会话时成员数量不正确。"""
    # Arrange
    user1_id = uuid4()
    actor1 = Actor.from_user(user1_id)

    # Mock repository
    mock_repo = AsyncMock()

    # Create handler
    handler = CreateConversationCommandHandler(mock_repo)

    # Create command with only 1 member
    command = CreateConversationCommand(
        conversation_type="direct",
        members=[actor1],  # 只有1个成员
        creator=actor1,
    )

    # Act & Assert
    with pytest.raises(DomainException, match="must have exactly 2 members"):
        await handler.handle(command)


@pytest.mark.asyncio
async def test_create_group_conversation_insufficient_members():
    """测试创建群聊时成员数量不足。"""
    # Arrange
    user1_id = uuid4()
    actor1 = Actor.from_user(user1_id)

    # Mock repository
    mock_repo = AsyncMock()

    # Create handler
    handler = CreateConversationCommandHandler(mock_repo)

    # Create command with only 1 member
    command = CreateConversationCommand(
        conversation_type="group",
        members=[actor1],  # 只有1个成员
        title="Test Group",
        creator=actor1,
    )

    # Act & Assert
    with pytest.raises(DomainException, match="must have at least 2 members"):
        await handler.handle(command)
