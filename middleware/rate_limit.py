"""
Rate Limiting Middleware — Athar Bot
حماية البوت من الإساءة والإغراق
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

logger = logging.getLogger(__name__)

RATE_PER_MINUTE = 20
RATE_PER_HOUR = 100
ADMIN_EXEMPT_IDS: set = set()


class RateLimitMiddleware(BaseMiddleware):
    """Block users who send too many requests per minute or hour."""

    def __init__(self, admin_ids: list = None):
        super().__init__()
        self._minute_log: dict = defaultdict(list)
        self._hour_log: dict = defaultdict(list)
        self._warned: set = set()
        if admin_ids:
            ADMIN_EXEMPT_IDS.update(admin_ids)

    def _clean(self, user_id: int) -> None:
        now = datetime.now()
        m_ago = now - timedelta(minutes=1)
        h_ago = now - timedelta(hours=1)
        self._minute_log[user_id] = [t for t in self._minute_log[user_id] if t > m_ago]
        self._hour_log[user_id] = [t for t in self._hour_log[user_id] if t > h_ago]

    def _is_limited(self, user_id: int) -> str:
        """Return '' if OK, 'minute' or 'hour' if limited."""
        if user_id in ADMIN_EXEMPT_IDS:
            return ""
        self._clean(user_id)
        if len(self._minute_log[user_id]) >= RATE_PER_MINUTE:
            return "minute"
        if len(self._hour_log[user_id]) >= RATE_PER_HOUR:
            return "hour"
        return ""

    def _record(self, user_id: int) -> None:
        now = datetime.now()
        self._minute_log[user_id].append(now)
        self._hour_log[user_id].append(now)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None

        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None

        if user_id is None:
            return await handler(event, data)

        limit = self._is_limited(user_id)

        if isinstance(event, Message):
            if limit == "minute":
                if user_id not in self._warned:
                    self._warned.add(user_id)
                    await event.answer("⚠️ أرسلت كثيراً من الرسائل. انتظر دقيقة واحدة.")
                return
            if limit == "hour":
                if user_id not in self._warned:
                    self._warned.add(user_id)
                    await event.answer("⚠️ تجاوزت الحد المسموح. انتظر قليلاً.")
                return
            self._warned.discard(user_id)
            self._record(user_id)

        elif isinstance(event, CallbackQuery):
            if limit == "minute":
                await event.answer("⚠️ طلبات كثيرة جداً. انتظر دقيقة.", show_alert=True)
                return
            if limit == "hour":
                await event.answer("⚠️ تجاوزت الحد المسموح. انتظر قليلاً.", show_alert=True)
                return
            self._record(user_id)

        return await handler(event, data)
