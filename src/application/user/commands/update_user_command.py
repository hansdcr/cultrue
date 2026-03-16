"""更新用户命令。

处理更新用户信息的业务逻辑。
"""

from dataclasses import dataclass
from typing import Optional

from src.domain.user.repositories.user_repository import UserRepository
from src.domain.user.value_objects.user_id import UserId
from ..dtos.user_dto import UserDTO


@dataclass
class UpdateUserCommand:
    """更新用户命令。"""

    user_id: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class UpdateUserCommandHandler:
    """更新用户命令处理器。"""

    def __init__(self, user_repository: UserRepository) -> None:
        """初始化命令处理器。

        Args:
            user_repository: 用户仓储
        """
        self._user_repository = user_repository

    async def handle(self, command: UpdateUserCommand) -> UserDTO:
        """处理更新用户命令。

        Args:
            command: 更新用户命令

        Returns:
            用户DTO

        Raises:
            ValueError: 如果用户不存在
        """
        # 创建UserId值对象
        user_id = UserId.from_string(command.user_id)

        # 查找用户
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID '{command.user_id}' not found")

        # 更新用户资料
        user.update_profile(
            full_name=command.full_name,
            avatar_url=command.avatar_url,
            bio=command.bio,
        )

        # 保存更新
        await self._user_repository.update(user)

        # 返回用户DTO
        return UserDTO.from_entity(user)
