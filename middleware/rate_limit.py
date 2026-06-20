"""
Rate Limiting Middleware — Athar Bot
حماية البوت من الإساءة والإغراق
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

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

    async def on_process_message(self, message: types.Message, data: dict):
        user_id = message.from_user.id
        limit = self._is_limited(user_id)
        if limit == "minute":
            if user_id not in self._warned:
                self._warned.add(user_id)
                await message.answer("⚠️ أرسلت كثيراً من الرسائل. انتظر دقيقة واحدة.")
            raise CancelHandler()
        if limit == "hour":
            if user_id not in self._warned:
                self._warned.add(user_id)
                await message.answer("⚠️ تجاوزت الحد المسموح. انتظر قليلاً.")
            raise CancelHandler()
        self._warned.discard(user_id)
        self._record(user_id)

    async def on_process_callback_query(self, call: types.CallbackQuery, data: dict):
        user_id = call.from_user.id
        limit = self._is_limited(user_id)
        if limit == "minute":
            await call.answer("⚠️ طلبات كثيرة جداً. انتظر دقيقة.", show_alert=True)
            raise CancelHandler()
        if limit == "hour":
            await call.answer("⚠️ تجاوزت الحد المسموح. انتظر قليلاً.", show_alert=True)
            raise CancelHandler()
        self._record(user_id)
