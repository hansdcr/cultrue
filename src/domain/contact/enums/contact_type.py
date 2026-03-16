"""Contact type enumeration."""
from enum import Enum


class ContactType(str, Enum):
    """联系人类型枚举。"""
    FRIEND = "friend"        # 好友
    FAVORITE = "favorite"    # 收藏
    COLLEAGUE = "colleague"  # 同事
    BLOCKED = "blocked"      # 屏蔽
