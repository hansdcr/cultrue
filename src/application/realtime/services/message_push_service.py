"""Message push service."""
import logging
from datetime import datetime, timezone
from typing import Dict
from uuid import UUID

from src.application.realtime.services.connection_manager import ConnectionManager
from src.domain.messaging.events.message_event import MessageEvent
from src.domain.messaging.repositories.conversation_repository import ConversationRepository
from src.domain.shared.value_objects.actor import Actor

logger = logging.getLogger(__name__)


class MessagePushService:
    """消息推送服务。"""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        conversation_repo: ConversationRepository
    ):
        """初始化消息推送服务。

        Args:
            connection_manager: 连接管理器
            conversation_repo: 会话仓储
        """
        self.connection_manager = connection_manager
        self.conversation_repo = conversation_repo

    async def push_message_to_conversation(
        self,
        conversation_id: UUID,
        message_event: MessageEvent,
        exclude_sender: bool = True
    ) -> Dict[str, int]:
        """推送消息到会话的所有在线成员。

        Args:
            conversation_id: 会话ID
            message_event: 消息事件
            exclude_sender: 是否排除发送者

        Returns:
            推送统计 {"success": 3, "failed": 0, "offline": 2}
        """
        # 1. 获取会话成员
        conversation = await self.conversation_repo.find_by_id(conversation_id)
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found")
            return {"success": 0, "failed": 0, "offline": 0}

        # 2. 构造推送消息
        push_data = {
            "type": "new_message",
            "data": {
                "message_id": str(message_event.message_id),
                "conversation_id": str(message_event.conversation_id),
                "sender": {
                    "actor_type": message_event.sender.actor_type.value,
                    "actor_id": str(message_event.sender.actor_id)
                },
                "message_type": message_event.message_type,
                "content": message_event.content,
                "metadata": message_event.metadata,
                "created_at": message_event.created_at.isoformat()
            }
        }

        # 3. 推送给所有在线成员
        stats = {"success": 0, "failed": 0, "offline": 0}

        for member in conversation.members:
            # 排除发送者（可选）
            if exclude_sender and member == message_event.sender:
                continue

            # 检查在线状态
            if not self.connection_manager.is_online(member):
                stats["offline"] += 1
                continue

            # 推送到所有设备
            connections = self.connection_manager.get_connections(member)
            for ws in connections:
                try:
                    await ws.send_json(push_data)
                    stats["success"] += 1
                except Exception as e:
                    logger.error(f"Failed to push message to {member}: {e}")
                    stats["failed"] += 1

        logger.info(
            f"Pushed message {message_event.message_id} to conversation {conversation_id}: "
            f"success={stats['success']}, failed={stats['failed']}, offline={stats['offline']}"
        )

        return stats

    async def push_to_actor(
        self,
        actor: Actor,
        message_type: str,
        data: dict
    ) -> int:
        """推送消息给特定Actor的所有设备。

        Args:
            actor: Actor值对象
            message_type: 消息类型
            data: 消息数据

        Returns:
            成功推送的设备数量
        """
        if not self.connection_manager.is_online(actor):
            logger.debug(f"Actor {actor} is offline, skipping push")
            return 0

        push_data = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        connections = self.connection_manager.get_connections(actor)
        success_count = 0

        for ws in connections:
            try:
                await ws.send_json(push_data)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to push to {actor}: {e}")

        logger.debug(f"Pushed {message_type} to {actor}: {success_count} devices")

        return success_count
