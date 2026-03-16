"""获取用户查询。

处理获取用户信息的查询逻辑。
"""

from dataclasses import dataclass

from src.domain.user.repositories.user_repository import UserRepository
from src.domain.user.value_objects.user_id import UserId
from ..dtos.user_dto import UserDTO


@dataclass
class GetUserQuery:
    """获取用户查询。"""

    user_id: str


class GetUserQueryHandler:
    """获取用户查询处理器。"""

    def __init__(self, user_repository: UserRepository) -> None:
        """初始化查询处理器。

        Args:
            user_repository: 用户仓储
        """
        self._user_repository = user_repository

    async def handle(self, query: GetUserQuery) -> UserDTO:
        """处理获取用户查询。

        Args:
            query: 获取用户查询

        Returns:
            用户DTO

        Raises:
            ValueError: 如果用户不存在
        """
        # 创建UserId值对象
        user_id = UserId.from_string(query.user_id)

        # 查找用户
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID '{query.user_id}' not found")

        # 返回用户DTO
        return UserDTO.from_entity(user)
