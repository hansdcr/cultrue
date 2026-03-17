"""WebSocket认证模块。

支持User JWT和Agent API Key两种认证方式。
"""
import logging
from uuid import UUID

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from src.domain.agent.value_objects.api_key import ApiKey
from src.domain.shared.value_objects.actor import Actor
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.repositories.postgres_agent_repository import (
    PostgresAgentRepository,
)
from src.infrastructure.security.jwt_service import (
    JWTExpiredError,
    JWTInvalidError,
    jwt_service,
)

logger = logging.getLogger(__name__)


async def authenticate_websocket(
    websocket: WebSocket,
    token: str = None,
    api_key: str = None,
) -> Actor:
    """WebSocket连接认证。

    支持两种认证方式：
    1. token参数 - User JWT认证
    2. api_key参数 - Agent API Key认证

    Args:
        websocket: WebSocket连接
        token: JWT token（User认证）
        api_key: API Key（Agent认证）

    Returns:
        Actor值对象

    Raises:
        WebSocketDisconnect: 认证失败时关闭连接
    """
    if token:
        return await _authenticate_user(websocket, token)
    elif api_key:
        return await _authenticate_agent(websocket, api_key)
    else:
        await websocket.close(code=4000, reason="Missing credentials")
        raise WebSocketDisconnect(code=4000)


async def _authenticate_user(websocket: WebSocket, token: str) -> Actor:
    """User JWT认证。

    Args:
        websocket: WebSocket连接
        token: JWT token

    Returns:
        Actor值对象

    Raises:
        WebSocketDisconnect: 认证失败时关闭连接
    """
    try:
        user_id = jwt_service.get_user_id_from_token(token)
        return Actor.from_user(UUID(user_id))
    except (JWTExpiredError, JWTInvalidError) as e:
        logger.warning(f"WebSocket JWT authentication failed: {e}")
        await websocket.close(code=4001, reason="Invalid token")
        raise WebSocketDisconnect(code=4001)
    except Exception as e:
        logger.error(f"WebSocket user authentication error: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        raise WebSocketDisconnect(code=4001)


async def _authenticate_agent(websocket: WebSocket, api_key_str: str) -> Actor:
    """Agent API Key认证。

    Args:
        websocket: WebSocket连接
        api_key_str: API Key字符串

    Returns:
        Actor值对象

    Raises:
        WebSocketDisconnect: 认证失败时关闭连接
    """
    try:
        api_key = ApiKey(api_key_str)
    except ValueError as e:
        logger.warning(f"WebSocket API Key format error: {e}")
        await websocket.close(code=4001, reason="Invalid API Key format")
        raise WebSocketDisconnect(code=4001)

    try:
        async for session in get_db_session():
            agent_repo = PostgresAgentRepository(session)

            # 使用前缀快速查找Agent
            prefix = api_key.get_prefix()
            agent = await agent_repo.find_by_api_key_prefix(prefix)

            if not agent:
                await websocket.close(code=4001, reason="Invalid API Key")
                raise WebSocketDisconnect(code=4001)

            # 验证完整的API Key
            if not agent.verify_api_key(api_key):
                await websocket.close(code=4001, reason="Invalid API Key")
                raise WebSocketDisconnect(code=4001)

            # 检查Agent是否激活
            if not agent.is_active:
                await websocket.close(code=4001, reason="Agent is not active")
                raise WebSocketDisconnect(code=4001)

            return Actor.from_agent(agent.id)

    except WebSocketDisconnect:
        raise
    except Exception as e:
        logger.error(f"WebSocket agent authentication error: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        raise WebSocketDisconnect(code=4001)
