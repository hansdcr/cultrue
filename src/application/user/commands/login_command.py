"""登录命令。

处理用户登录的业务逻辑。
"""

from dataclasses import dataclass

from src.domain.user.repositories.user_repository import UserRepository
from src.domain.user.value_objects.email import Email
from src.infrastructure.security.jwt_service import jwt_service
from src.infrastructure.security.password_hasher import password_hasher
from ..dtos.user_dto import UserDTO


@dataclass
class LoginCommand:
    """登录命令。"""

    email: str
    password: str


@dataclass
class LoginResult:
    """登录结果。"""

    user: UserDTO
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginCommandHandler:
    """登录命令处理器。"""

    def __init__(self, user_repository: UserRepository) -> None:
        """初始化命令处理器。

        Args:
            user_repository: 用户仓储
        """
        self._user_repository = user_repository

    async def handle(self, command: LoginCommand) -> LoginResult:
        """处理登录命令。

        Args:
            command: 登录命令

        Returns:
            登录结果

        Raises:
            ValueError: 如果邮箱或密码错误，或用户未激活
        """
        # 创建Email值对象
        email = Email.from_string(command.email)

        # 查找用户
        user = await self._user_repository.find_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")

        # 验证密码
        if not password_hasher.verify_password(command.password, user.password_hash):
            raise ValueError("Invalid email or password")

        # 检查用户是否激活
        if not user.is_active:
            raise ValueError("User account is not active")

        # 记录登录时间
        user.record_login()
        await self._user_repository.update(user)

        # 生成JWT Token
        access_token = jwt_service.create_access_token(str(user.id))
        refresh_token = jwt_service.create_refresh_token(str(user.id))

        # 返回登录结果
        return LoginResult(
            user=UserDTO.from_entity(user),
            access_token=access_token,
            refresh_token=refresh_token,
        )
