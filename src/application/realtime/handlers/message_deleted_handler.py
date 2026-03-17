"""Message deleted event handler."""
import logging

from src.application.realtime.services.message_push_service import MessagePushService
from src.application.shared.events.event_handler import EventHandler
from src.domain.messaging.events.message_event import MessageEvent

logger = logging.getLogger(__name__)


class MessageDeletedEventHandler(EventHandler):
    """消息删除事件处理器。"""

    def __init__(self, push_service: MessagePushService):
        """初始化处理器。

        Args:
            push_service: 消息推送服务
        """
        self.push_service = push_service

    async def handle(self, event: MessageEvent) -> None:
        """处理消息删除事件。

        Args:
            event: 消息事件
        """
        try:
            # 通知会话成员消息已删除
            stats = await self.push_service.push_message_to_conversation(
                event.conversation_id,
                event,
                exclude_sender=False  # 包括发送者
            )

            logger.info(
                f"Message deletion {event.message_id} notified: "
                f"success={stats['success']}, "
                f"failed={stats['failed']}, "
                f"offline={stats['offline']}"
            )
        except Exception as e:
            logger.error(f"Failed to handle message_deleted event: {e}", exc_info=True)
