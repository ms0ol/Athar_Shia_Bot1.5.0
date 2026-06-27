"""
handlers/__init__.py — تجميع وربط كل الـ Routers في راوتر رئيسي واحد
"""

from aiogram import Router

from .common import router as common_router
from .ibadat import router as ibadat_router
from .prayer import router as prayer_router
from .events import router as events_router
from .daily import router as daily_router
from .admin import router as admin_router

main_router = Router(name="main_handlers_router")

main_router.include_routers(
    common_router,
    ibadat_router,
    prayer_router,
    events_router,
    daily_router,
    admin_router,
)
