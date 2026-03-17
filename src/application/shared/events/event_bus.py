"""Event bus for publish-subscribe pattern."""
import asyncio
import logging
from typing import Callable, Dict, List

from src.domain.messaging.events.message_event import MessageEvent

logger = logging.getLogger(__name__)


class EventBus:
    """事件总线（内存实现）。"""

    def __init__(self):
        """初始化事件总线。"""
        self._handlers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """订阅事件。

        Args:
            event_type: 事件类型
            handler: 事件处理器（异步函数）
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Subscribed handler {handler.__name__} to event {event_type}")

    async def publish(self, event: MessageEvent) -> None:
        """发布事件。

        Args:
            event: 消息事件
        """
        handlers = self._handlers.get(event.event_type, [])

        if not handlers:
            logger.debug(f"No handlers for event type: {event.event_type}")
            return

        logger.debug(f"Publishing event {event.event_type} to {len(handlers)} handlers")

        # 异步执行所有处理器
        results = await asyncio.gather(
            *[handler(event) for handler in handlers],
            return_exceptions=True
        )

        # 记录错误
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Handler {handlers[i].__name__} failed for event {event.event_type}: {result}",
                    exc_info=result
                )
