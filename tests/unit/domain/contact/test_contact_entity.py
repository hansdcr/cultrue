"""Test Contact entity."""
from uuid import uuid4

from src.domain.contact.entities.contact import Contact
from src.domain.contact.enums.contact_type import ContactType
from src.domain.shared.value_objects.actor import Actor


def test_create_contact():
    """测试创建Contact。"""
    owner = Actor.from_user(uuid4())
    target = Actor.from_agent(uuid4())

    contact = Contact.create(
        owner=owner,
        target=target,
        contact_type=ContactType.FRIEND,
        alias="My AI Assistant",
    )

    assert contact.owner == owner
    assert contact.target == target
    assert contact.contact_type == ContactType.FRIEND
    assert contact.alias == "My AI Assistant"
    assert not contact.is_favorite


def test_contact_mark_as_favorite():
    """测试标记为收藏。"""
    owner = Actor.from_user(uuid4())
    target = Actor.from_agent(uuid4())

    contact = Contact.create(owner=owner, target=target)

    assert not contact.is_favorite

    contact.mark_as_favorite()

    assert contact.is_favorite
    assert contact.contact_type == ContactType.FAVORITE


def test_contact_update_alias():
    """测试更新别名。"""
    owner = Actor.from_user(uuid4())
    target = Actor.from_agent(uuid4())

    contact = Contact.create(owner=owner, target=target)

    contact.update_alias("New Alias")

    assert contact.alias == "New Alias"


def test_contact_block_unblock():
    """测试屏蔽/取消屏蔽。"""
    owner = Actor.from_user(uuid4())
    target = Actor.from_agent(uuid4())

    contact = Contact.create(owner=owner, target=target)

    # 屏蔽
    contact.block()
    assert contact.contact_type == ContactType.BLOCKED

    # 取消屏蔽
    contact.unblock()
    assert contact.contact_type == ContactType.FRIEND


def test_contact_record_interaction():
    """测试记录交互时间。"""
    owner = Actor.from_user(uuid4())
    target = Actor.from_agent(uuid4())

    contact = Contact.create(owner=owner, target=target)

    assert contact.last_interaction_at is None

    contact.record_interaction()

    assert contact.last_interaction_at is not None


def test_contact_user_to_user():
    """测试User-User联系人关系。"""
    owner = Actor.from_user(uuid4())
    target = Actor.from_user(uuid4())

    contact = Contact.create(owner=owner, target=target)

    assert contact.owner.is_user()
    assert contact.target.is_user()


def test_contact_agent_to_agent():
    """测试Agent-Agent联系人关系。"""
    owner = Actor.from_agent(uuid4())
    target = Actor.from_agent(uuid4())

    contact = Contact.create(owner=owner, target=target)

    assert contact.owner.is_agent()
    assert contact.target.is_agent()
