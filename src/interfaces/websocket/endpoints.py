"""WebSocket端点。

提供WebSocket连接管理和实时通信功能。
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends

from src.application.realtime.services.connection_manager import ConnectionManager
from src.application.realtime.services.online_status_service import OnlineStatusService
from src.domain.messaging.repositories.conversation_repository import ConversationRepository
from src.interfaces.websocket.auth import authenticate_websocket

logger = logging.getLogger(__name__)

router = APIRouter()


# 全局实例（将在main.py中初始化）
_connection_manager: ConnectionManager = None
_online_status_service: OnlineStatusService = None
_conversation_repo: ConversationRepository = None


def get_connection_manager() -> ConnectionManager:
    """获取ConnectionManager实例。

    Returns:
        ConnectionManager实例
    """
    return _connection_manager


def get_online_status_service() -> OnlineStatusService:
    """获取OnlineStatusService实例。

    Returns:
        OnlineStatusService实例
    """
    return _online_status_service


def get_conversation_repo() -> ConversationRepository:
    """获取ConversationRepository实例。

    Returns:
        ConversationRepository实例
    """
    return _conversation_repo


def set_connection_manager(manager: ConnectionManager) -> None:
    """设置ConnectionManager实例。

    Args:
        manager: ConnectionManager实例
    """
    global _connection_manager
    _connection_manager = manager


def set_online_status_service(service: OnlineStatusService) -> None:
    """设置OnlineStatusService实例。

    Args:
        service: OnlineStatusService实例
    """
    global _online_status_service
    _online_status_service = service


def set_conversation_repo(repo: ConversationRepository) -> None:
    """设置ConversationRepository实例。

    Args:
        repo: ConversationRepository实例
    """
    global _conversation_repo
    _conversation_repo = repo


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None),
    api_key: str = Query(None),
    connection_manager: ConnectionManager = Depends(get_connection_manager),
    online_status_service: OnlineStatusService = Depends(get_online_status_service),
    conversation_repo: ConversationRepository = Depends(get_conversation_repo),
):
    """WebSocket连接端点。

    连接URL示例：
    - User: ws://localhost:8000/ws?token=<jwt_token>
    - Agent: ws://localhost:8000/ws?api_key=<api_key>
    """
    await websocket.accept()

    actor = None
    try:
        # 认证
        actor = await authenticate_websocket(websocket, token, api_key)

        # 注册连接
        metadata = {
            "user_agent": websocket.headers.get("user-agent"),
            "client_ip": websocket.client.host if websocket.client else None,
        }
        connection = await connection_manager.connect(websocket, actor, metadata)

        # 通知在线状态（如果有conversation_repo）
        if online_status_service and conversation_repo:
            conversations = await conversation_repo.find_by_actor(actor)
            conversation_ids = [conv.id for conv in conversations]
            await online_status_service.notify_status_change(actor, "online", conversation_ids)

        # 发送连接成功消息
        await websocket.send_json({
            "type": "connection_established",
            "data": {
                "connection_id": str(connection.id),
                "actor_type": actor.actor_type.value,
                "actor_id": str(actor.actor_id),
                "connected_at": connection.connected_at.isoformat(),
            },
        })

        # 消息循环
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "ping":
                await connection_manager.update_heartbeat(websocket)
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            elif message_type == "ack":
                # 消息送达确认
                message_id = data.get("message_id")
                logger.info(f"Message {message_id} acknowledged by {actor}")

            elif message_type == "typing":
                # 输入状态推送（暂不实现）
                logger.debug(f"Typing event from {actor}")

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        # 清理连接
        await connection_manager.disconnect(websocket)

        # 通知离线状态
        if actor and online_status_service and conversation_repo:
            try:
                conversations = await conversation_repo.find_by_actor(actor)
                conversation_ids = [conv.id for conv in conversations]
                await online_status_service.notify_status_change(actor, "offline", conversation_ids)
            except Exception as e:
                logger.error(f"Failed to notify offline status: {e}")
