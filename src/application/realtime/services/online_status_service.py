"""Online status service."""
import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from src.application.realtime.services.connection_manager import ConnectionManager
from src.application.realtime.services.message_push_service import MessagePushService
from src.domain.messaging.repositories.conversation_repository import ConversationRepository
from src.domain.shared.value_objects.actor import Actor

logger = logging.getLogger(__name__)


class OnlineStatusService:
    """在线状态服务。"""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        push_service: MessagePushService,
        conversation_repo: ConversationRepository
    ):
        """初始化在线状态服务。

        Args:
            connection_manager: 连接管理器
            push_service: 消息推送服务
            conversation_repo: 会话仓储
        """
        self.connection_manager = connection_manager
        self.push_service = push_service
        self.conversation_repo = conversation_repo

    def is_online(self, actor: Actor) -> bool:
        """检查Actor是否在线。

        Args:
            actor: Actor值对象

        Returns:
            是否在线
        """
        return self.connection_manager.is_online(actor)

    def get_online_members(self, actors: List[Actor]) -> List[Actor]:
        """获取在线的成员列表。

        Args:
            actors: Actor列表

        Returns:
            在线的Actor列表
        """
        return [actor for actor in actors if self.is_online(actor)]

    async def notify_status_change(
        self,
        actor: Actor,
        status: str,  # "online" or "offline"
        conversation_ids: List[UUID]
    ) -> None:
        """通知会话成员Actor的在线状态变更。

        Args:
            actor: 状态变更的Actor
            status: 新状态（"online" 或 "offline"）
            conversation_ids: 需要通知的会话ID列表
        """
        notification_data = {
            "actor_type": actor.actor_type.value,
            "actor_id": str(actor.actor_id),
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        logger.info(f"Notifying status change: {actor} is now {status}")

        # 推送给相关会话的在线成员
        notified_count = 0
        for conv_id in conversation_ids:
            conversation = await self.conversation_repo.find_by_id(conv_id)
            if not conversation:
                continue

            for member in conversation.members:
                if member == actor:  # 不推送给自己
                    continue

                count = await self.push_service.push_to_actor(
                    member,
                    "status_change",
                    notification_data
                )
                notified_count += count

        logger.info(f"Status change notification sent to {notified_count} devices")
