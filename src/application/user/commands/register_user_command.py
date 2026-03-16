"""注册用户命令。

处理用户注册的业务逻辑。
"""

from dataclasses import dataclass
from typing import Optional

from src.domain.user.entities.user import User
from src.domain.user.repositories.user_repository import UserRepository
from src.domain.user.value_objects.email import Email
from src.infrastructure.security.password_hasher import password_hasher
from ..dtos.user_dto import UserDTO


@dataclass
class RegisterUserCommand:
    """注册用户命令。"""

    username: str
    email: str
    password: str
    full_name: Optional[str] = None


class RegisterUserCommandHandler:
    """注册用户命令处理器。"""

    def __init__(self, user_repository: UserRepository) -> None:
        """初始化命令处理器。

        Args:
            user_repository: 用户仓储
        """
        self._user_repository = user_repository

    async def handle(self, command: RegisterUserCommand) -> UserDTO:
        """处理注册用户命令。

        Args:
            command: 注册用户命令

        Returns:
            用户DTO

        Raises:
            ValueError: 如果用户名或邮箱已存在
        """
        # 验证用户名是否已存在
        if await self._user_repository.exists_by_username(command.username):
            raise ValueError(f"Username '{command.username}' already exists")

        # 创建Email值对象（会自动验证格式）
        email = Email.from_string(command.email)

        # 验证邮箱是否已存在
        if await self._user_repository.exists_by_email(email):
            raise ValueError(f"Email '{command.email}' already exists")

        # 加密密码
        password_hash = password_hasher.hash_password(command.password)

        # 创建用户实体
        user = User.create(
            username=command.username,
            email=email,
            password_hash=password_hash,
            full_name=command.full_name,
        )

        # 保存用户
        await self._user_repository.save(user)

        # 返回用户DTO
        return UserDTO.from_entity(user)
