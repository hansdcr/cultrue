"""Messaging system integration tests.

测试会话和消息仓储的集成功能。
"""

import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.infrastructure.config import settings
from src.infrastructure.persistence.models import (
    ConversationModel,
    ConversationMemberModel,
    MessageModel,
    ParticipantModel,
    UserModel,
    AgentModel,
)
from src.infrastructure.persistence.repositories.postgres_participant_repository import PostgresParticipantRepository
from src.infrastructure.persistence.repositories.postgres_conversation_repository import PostgresConversationRepository
from src.infrastructure.persistence.repositories.postgres_message_repository import PostgresMessageRepository
from src.domain.messaging.entities.conversation import Conversation
from src.domain.messaging.entities.message import Message
from src.domain.messaging.enums.conversation_type import ConversationType
from src.domain.messaging.enums.conversation_status import ConversationStatus
from src.domain.messaging.enums.message_type import MessageType
from src.domain.messaging.value_objects.conversation_id import ConversationId
from src.domain.shared.value_objects.actor import Actor


@pytest.fixture(scope="module")
def engine():
    """创建测试数据库引擎。"""
    database_url = settings.database_url.replace(
        "postgresql+asyncpg", "postgresql"
    )
    engine = create_engine(database_url)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine):
    """创建测试数据库会话。"""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session):
    """创建测试用户。"""
    user = UserModel(
        id=uuid.uuid4(),
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed_password",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def test_agent(db_session):
    """创建测试Agent。"""
    agent = AgentModel(
        id=uuid.uuid4(),
        agent_id=f"agent_{uuid.uuid4().hex[:16]}",
        name=f"TestAgent_{uuid.uuid4().hex[:8]}",
        description="Test agent",
        system_prompt="You are a test agent",
        model_config={"model": "gpt-4", "temperature": 0.7, "max_tokens": 1000},
        api_key_prefix="test_prefix",
        api_key_hash="test_hash",
        is_active=True
    )
    db_session.add(agent)
    db_session.flush()
    return agent


class TestConversationRepository:
    """ConversationRepository集成测试。"""

    def test_conversation_members_created(self, db_session, test_user, test_agent):
        """测试会话成员记录创建。"""
        # 创建participants
        user_participant = ParticipantModel(
            id=uuid.uuid4(),
            participant_type="user",
            user_id=test_user.id,
            agent_id=None
        )
        agent_participant = ParticipantModel(
            id=uuid.uuid4(),
            participant_type="agent",
            user_id=None,
            agent_id=test_agent.id
        )
        db_session.add(user_participant)
        db_session.add(agent_participant)
        db_session.flush()

        # 创建会话
        conversation = ConversationModel(
            id=uuid.uuid4(),
            conversation_type="direct",
            status="active",
            message_count=0
        )
        db_session.add(conversation)
        db_session.flush()

        # 创建会话成员
        member1 = ConversationMemberModel(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            participant_id=user_participant.id
        )
        member2 = ConversationMemberModel(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            participant_id=agent_participant.id
        )
        db_session.add(member1)
        db_session.add(member2)
        db_session.commit()

        # 验证
        stmt = select(ConversationMemberModel).where(
            ConversationMemberModel.conversation_id == conversation.id
        )
        result = db_session.execute(stmt)
        members = result.scalars().all()

        assert len(members) == 2

    def test_group_conversation(self, db_session, test_user, test_agent):
        """测试群聊创建。"""
        # 创建participants
        user_participant = ParticipantModel(
            id=uuid.uuid4(),
            participant_type="user",
            user_id=test_user.id,
            agent_id=None
        )
        agent_participant = ParticipantModel(
            id=uuid.uuid4(),
            participant_type="agent",
            user_id=None,
            agent_id=test_agent.id
        )
        db_session.add(user_participant)
        db_session.add(agent_participant)
        db_session.flush()

        # 创建群聊
        conversation = ConversationModel(
            id=uuid.uuid4(),
            conversation_type="group",
            title="Test Group",
            status="active",
            message_count=0
        )
        db_session.add(conversation)
        db_session.commit()

        # 验证
        stmt = select(ConversationModel).where(
            ConversationModel.id == conversation.id
        )
        result = db_session.execute(stmt)
        conv = result.scalar_one()

        assert conv.conversation_type == "group"
        assert conv.title == "Test Group"


class TestMessageRepository:
    """MessageRepository集成测试。"""

    def test_create_message(self, db_session, test_user, test_agent):
        """测试创建消息。"""
        # 创建participants
        user_participant = ParticipantModel(
            id=uuid.uuid4(),
            participant_type="user",
            user_id=test_user.id,
            agent_id=None
        )
        db_session.add(user_participant)
        db_session.flush()

        # 创建会话
        conversation = ConversationModel(
            id=uuid.uuid4(),
            conversation_type="direct",
            status="active",
            message_count=0
        )
        db_session.add(conversation)
        db_session.flush()

        # 创建消息
        message = MessageModel(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            sender_id=user_participant.id,
            message_type="text",
            content="Hello, world!",
            message_metadata={"key": "value"}
        )
        db_session.add(message)
        db_session.commit()

        # 验证
        stmt = select(MessageModel).where(MessageModel.id == message.id)
        result = db_session.execute(stmt)
        msg = result.scalar_one()

        assert msg.content == "Hello, world!"
        assert msg.message_type == "text"
        assert msg.message_metadata == {"key": "value"}

    def test_message_count_trigger(self, db_session, test_user):
        """测试消息计数触发器。"""
        # 创建participant
        user_participant = ParticipantModel(
            id=uuid.uuid4(),
            participant_type="user",
            user_id=test_user.id,
            agent_id=None
        )
        db_session.add(user_participant)
        db_session.flush()

        # 创建会话
        conversation = ConversationModel(
            id=uuid.uuid4(),
            conversation_type="direct",
            status="active",
            message_count=0
        )
        db_session.add(conversation)
        db_session.flush()

        # 创建消息
        message = MessageModel(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            sender_id=user_participant.id,
            message_type="text",
            content="Test message"
        )
        db_session.add(message)
        db_session.commit()

        # 刷新会话对象
        db_session.refresh(conversation)

        # 验证message_count自动增加
        assert conversation.message_count == 1
        assert conversation.last_message_at is not None


class TestMessagingScenarios:
    """消息系统场景测试。"""

    def test_user_to_user_scenario(self, db_session):
        """测试User ↔ User通信场景。"""
        # 创建两个用户
        user1 = UserModel(
            id=uuid.uuid4(),
            username=f"user1_{uuid.uuid4().hex[:8]}",
            email=f"user1_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="hash1"
        )
        user2 = UserModel(
            id=uuid.uuid4(),
            username=f"user2_{uuid.uuid4().hex[:8]}",
            email=f"user2_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="hash2"
        )
        db_session.add(user1)
        db_session.add(user2)
        db_session.flush()

        # 创建participants
        p1 = ParticipantModel(
            id=uuid.uuid4(),
            participant_type="user",
            user_id=user1.id
        )
        p2 = ParticipantModel(
            id=uuid.uuid4(),
            participant_type="user",
            user_id=user2.id
        )
        db_session.add(p1)
        db_session.add(p2)
        db_session.flush()

        # 创建会话
        conv = ConversationModel(
            id=uuid.uuid4(),
            conversation_type="direct",
            status="active",
            message_count=0
        )
        db_session.add(conv)
        db_session.flush()

        # 添加成员
        db_session.add(ConversationMemberModel(
            id=uuid.uuid4(),
            conversation_id=conv.id,
            participant_id=p1.id
        ))
        db_session.add(ConversationMemberModel(
            id=uuid.uuid4(),
            conversation_id=conv.id,
            participant_id=p2.id
        ))
        db_session.commit()

        # 验证
        stmt = select(ConversationMemberModel).where(
            ConversationMemberModel.conversation_id == conv.id
        )
        result = db_session.execute(stmt)
        members = result.scalars().all()

        assert len(members) == 2

    def test_user_to_agent_scenario(self, db_session, test_user, test_agent):
        """测试User ↔ Agent通信场景。"""
        # 创建participants
        user_p = ParticipantModel(
            id=uuid.uuid4(),
            participant_type="user",
            user_id=test_user.id
        )
        agent_p = ParticipantModel(
            id=uuid.uuid4(),
            participant_type="agent",
            agent_id=test_agent.id
        )
        db_session.add(user_p)
        db_session.add(agent_p)
        db_session.flush()

        # 创建会话
        conv = ConversationModel(
            id=uuid.uuid4(),
            conversation_type="direct",
            status="active",
            message_count=0
        )
        db_session.add(conv)
        db_session.flush()

        # 添加成员
        db_session.add(ConversationMemberModel(
            id=uuid.uuid4(),
            conversation_id=conv.id,
            participant_id=user_p.id
        ))
        db_session.add(ConversationMemberModel(
            id=uuid.uuid4(),
            conversation_id=conv.id,
            participant_id=agent_p.id
        ))
        db_session.commit()

        # 验证
        assert conv.conversation_type == "direct"
