"""WebSocket端点。

提供WebSocket连接管理和实时通信功能。
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends

from src.application.realtime.services.connection_manager import ConnectionManager
from src.interfaces.websocket.auth import authenticate_websocket

logger = logging.getLogger(__name__)

router = APIRouter()


# 全局ConnectionManager实例（将在main.py中初始化）
_connection_manager: ConnectionManager = None


def get_connection_manager() -> ConnectionManager:
    """获取ConnectionManager实例。

    Returns:
        ConnectionManager实例
    """
    return _connection_manager


def set_connection_manager(manager: ConnectionManager) -> None:
    """设置ConnectionManager实例。

    Args:
        manager: ConnectionManager实例
    """
    global _connection_manager
    _connection_manager = manager


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None),
    api_key: str = Query(None),
    connection_manager: ConnectionManager = Depends(get_connection_manager),
):
    """WebSocket连接端点。

    连接URL示例：
    - User: ws://localhost:8000/ws?token=<jwt_token>
    - Agent: ws://localhost:8000/ws?api_key=<api_key>

    Args:
        websocket: WebSocket连接
        token: JWT token（User认证）
        api_key: API Key（Agent认证）
        connection_manager: 连接管理器
    """
    # 1. 接受连接
    await websocket.accept()

    try:
        # 2. 认证
        actor = await authenticate_websocket(websocket, token, api_key)

        # 3. 注册连接
        metadata = {
            "user_agent": websocket.headers.get("user-agent"),
            "client_ip": websocket.client.host if websocket.client else None,
        }
        connection = await connection_manager.connect(websocket, actor, metadata)

        # 4. 发送连接成功消息
        await websocket.send_json({
            "type": "connection_established",
            "data": {
                "connection_id": str(connection.id),
                "actor_type": actor.actor_type.value,
                "actor_id": str(actor.actor_id),
                "connected_at": connection.connected_at.isoformat(),
            },
        })

        # 5. 消息循环
        while True:
            # 接收消息
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "ping":
                # 心跳响应
                await connection_manager.update_heartbeat(websocket)
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            elif message_type == "message":
                # 消息发送（迭代10实现）
                await websocket.send_json({
                    "type": "error",
                    "message": "Message sending not yet implemented",
                })

            else:
                # 未知消息类型
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                })

    except WebSocketDisconnect:
        # 客户端断开连接
        logger.info("WebSocket client disconnected")
    except Exception as e:
        # 异常处理
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        # 6. 清理连接
        await connection_manager.disconnect(websocket)
