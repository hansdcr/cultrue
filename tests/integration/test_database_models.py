"""数据库模型集成测试。

测试所有数据库模型的CRUD操作、约束和关系。
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.infrastructure.config import settings
from src.infrastructure.persistence.database import Base
from src.infrastructure.persistence.models import (
    AgentModel,
    SessionModel,
    UserAgentModel,
    UserModel,
)


@pytest.fixture(scope="module")
def engine():
    """创建测试数据库引擎。"""
    # 使用同步引擎进行测试
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


class TestUserModel:
    """测试UserModel的CRUD操作和约束。"""

    def test_create_user(self, db_session):
        """测试创建用户。"""
        user = UserModel(
            id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User",
            wallet_balance=Decimal("100.00"),
            is_active=True,
            is_verified=False,
        )
        db_session.add(user)
        db_session.commit()

        # 验证用户已创建
        stmt = select(UserModel).where(UserModel.username == "testuser")
        result = db_session.execute(stmt).scalar_one()
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.wallet_balance == Decimal("100.00")

    def test_unique_username_constraint(self, db_session):
        """测试用户名唯一约束。"""
        user1 = UserModel(
            id=uuid.uuid4(),
            username="duplicate",
            email="user1@example.com",
            password_hash="hash1",
        )
        db_session.add(user1)
        db_session.commit()

        # 尝试创建相同用户名的用户
        user2 = UserModel(
            id=uuid.uuid4(),
            username="duplicate",
            email="user2@example.com",
            password_hash="hash2",
        )
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_unique_email_constraint(self, db_session):
        """测试邮箱唯一约束。"""
        user1 = UserModel(
            id=uuid.uuid4(),
            username="user1",
            email="duplicate@example.com",
            password_hash="hash1",
        )
        db_session.add(user1)
        db_session.commit()

        # 尝试创建相同邮箱的用户
        user2 = UserModel(
            id=uuid.uuid4(),
            username="user2",
            email="duplicate@example.com",
            password_hash="hash2",
        )
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestAgentModel:
    """测试AgentModel的CRUD操作和约束。"""

    def test_create_agent(self, db_session):
        """测试创建Agent。"""
        # 先创建一个用户作为创建者
        user = UserModel(
            id=uuid.uuid4(),
            username="creator",
            email="creator@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()

        # 创建Agent
        agent = AgentModel(
            id=uuid.uuid4(),
            agent_id="agent_test",
            name="Test Agent",
            description="A test agent",
            system_prompt="You are a test agent",
            model_config={"temperature": 0.7, "max_tokens": 1000},
            is_active=True,
            created_by=user.id,
        )
        db_session.add(agent)
        db_session.commit()

        # 验证Agent已创建
        stmt = select(AgentModel).where(AgentModel.agent_id == "agent_test")
        result = db_session.execute(stmt).scalar_one()
        assert result.name == "Test Agent"
        assert result.model_config["temperature"] == 0.7
        assert result.created_by == user.id

    def test_unique_agent_id_constraint(self, db_session):
        """测试agent_id唯一约束。"""
        agent1 = AgentModel(
            id=uuid.uuid4(),
            agent_id="duplicate_agent",
            name="Agent 1",
            is_active=True,
        )
        db_session.add(agent1)
        db_session.commit()

        # 尝试创建相同agent_id的Agent
        agent2 = AgentModel(
            id=uuid.uuid4(),
            agent_id="duplicate_agent",
            name="Agent 2",
            is_active=True,
        )
        db_session.add(agent2)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestSessionModel:
    """测试SessionModel的CRUD操作和约束。"""

    def test_create_session(self, db_session):
        """测试创建会话。"""
        # 先创建一个用户
        user = UserModel(
            id=uuid.uuid4(),
            username="sessionuser",
            email="session@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()

        # 创建会话
        session = SessionModel(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash="unique_token_hash",
            refresh_token_hash="refresh_hash",
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db_session.add(session)
        db_session.commit()

        # 验证会话已创建
        stmt = select(SessionModel).where(
            SessionModel.token_hash == "unique_token_hash"
        )
        result = db_session.execute(stmt).scalar_one()
        assert result.user_id == user.id
        assert result.refresh_token_hash == "refresh_hash"

    def test_unique_token_hash_constraint(self, db_session):
        """测试token_hash唯一约束。"""
        user = UserModel(
            id=uuid.uuid4(),
            username="tokenuser",
            email="token@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()

        session1 = SessionModel(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash="duplicate_token",
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db_session.add(session1)
        db_session.commit()

        # 尝试创建相同token_hash的会话
        session2 = SessionModel(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash="duplicate_token",
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db_session.add(session2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_cascade_delete_on_user(self, db_session):
        """测试删除用户时级联删除会话。"""
        user = UserModel(
            id=uuid.uuid4(),
            username="cascadeuser",
            email="cascade@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()

        session = SessionModel(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash="cascade_token",
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db_session.add(session)
        db_session.commit()

        # 删除用户
        db_session.delete(user)
        db_session.commit()

        # 验证会话也被删除
        stmt = select(SessionModel).where(
            SessionModel.token_hash == "cascade_token"
        )
        result = db_session.execute(stmt).scalar_one_or_none()
        assert result is None


class TestUserAgentModel:
    """测试UserAgentModel的CRUD操作和约束。"""

    def test_create_user_agent_association(self, db_session):
        """测试创建用户-Agent关联。"""
        # 创建用户
        user = UserModel(
            id=uuid.uuid4(),
            username="assocuser",
            email="assoc@example.com",
            password_hash="hash",
        )
        db_session.add(user)

        # 创建Agent
        agent = AgentModel(
            id=uuid.uuid4(),
            agent_id="agent_assoc",
            name="Assoc Agent",
            is_active=True,
        )
        db_session.add(agent)
        db_session.commit()

        # 创建关联
        user_agent = UserAgentModel(
            id=uuid.uuid4(),
            user_id=user.id,
            agent_id=agent.id,
            is_favorite=True,
        )
        db_session.add(user_agent)
        db_session.commit()

        # 验证关联已创建
        stmt = select(UserAgentModel).where(
            UserAgentModel.user_id == user.id,
            UserAgentModel.agent_id == agent.id,
        )
        result = db_session.execute(stmt).scalar_one()
        assert result.is_favorite is True

    def test_unique_user_agent_constraint(self, db_session):
        """测试用户-Agent唯一约束。"""
        user = UserModel(
            id=uuid.uuid4(),
            username="uniqueuser",
            email="unique@example.com",
            password_hash="hash",
        )
        db_session.add(user)

        agent = AgentModel(
            id=uuid.uuid4(),
            agent_id="agent_unique",
            name="Unique Agent",
            is_active=True,
        )
        db_session.add(agent)
        db_session.commit()

        # 创建第一个关联
        user_agent1 = UserAgentModel(
            id=uuid.uuid4(),
            user_id=user.id,
            agent_id=agent.id,
            is_favorite=False,
        )
        db_session.add(user_agent1)
        db_session.commit()

        # 尝试创建重复的关联
        user_agent2 = UserAgentModel(
            id=uuid.uuid4(),
            user_id=user.id,
            agent_id=agent.id,
            is_favorite=True,
        )
        db_session.add(user_agent2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_cascade_delete_on_user_and_agent(self, db_session):
        """测试删除用户或Agent时级联删除关联。"""
        user = UserModel(
            id=uuid.uuid4(),
            username="cascadeuser2",
            email="cascade2@example.com",
            password_hash="hash",
        )
        db_session.add(user)

        agent = AgentModel(
            id=uuid.uuid4(),
            agent_id="agent_cascade",
            name="Cascade Agent",
            is_active=True,
        )
        db_session.add(agent)
        db_session.commit()

        user_agent = UserAgentModel(
            id=uuid.uuid4(),
            user_id=user.id,
            agent_id=agent.id,
            is_favorite=False,
        )
        db_session.add(user_agent)
        db_session.commit()

        user_agent_id = user_agent.id

        # 删除Agent
        db_session.delete(agent)
        db_session.commit()

        # 验证关联也被删除
        stmt = select(UserAgentModel).where(UserAgentModel.id == user_agent_id)
        result = db_session.execute(stmt).scalar_one_or_none()
        assert result is None
