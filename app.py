"""
Athar Shia Bot - Main Entry Point
بوت أثر الشيعة - نقطة التشغيل الرئيسية
"""

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
import database as db
from handlers import router
from scheduler import BotScheduler
from middleware import RateLimitMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

PID_FILE = "/tmp/athar_bot.pid"


def acquire_pid_lock():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            logger.error(f"Another instance running (PID {old_pid}). Killing it...")
            os.kill(old_pid, 9)
            import time
            time.sleep(2)
        except (ValueError, ProcessLookupError, PermissionError):
            pass
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    logger.info(f"PID lock acquired (PID {os.getpid()})")


def release_pid_lock():
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            if pid == os.getpid():
                os.remove(PID_FILE)
    except Exception:
        pass


async def on_startup(bot: Bot, scheduler: BotScheduler):
    logger.info("Starting Athar Shia Bot...")

    await bot.delete_webhook(drop_pending_updates=False)
    logger.info("Webhook cleared")

    db.init_database()
    logger.info("Database initialized")

    await scheduler.start()

    from aiogram.types import BotCommand, BotCommandScopeChat
    base_commands = [
        BotCommand(command="start", description="بدء البوت وعرض القائمة الرئيسية"),
        BotCommand(command="menu", description="القائمة الرئيسية"),
        BotCommand(command="prayer", description="مواقيت الصلاة"),
        BotCommand(command="event", description="مناسبة اليوم"),
        BotCommand(command="daily", description="المحتوى اليومي"),
        BotCommand(command="subs", description="إدارة الاشتراكات"),
        BotCommand(command="city", description="تغيير المدينة"),
        BotCommand(command="about", description="المساعدة والأوامر"),
        BotCommand(command="id", description="الحصول على معرفك"),
    ]
    await bot.set_my_commands(base_commands)

    admin_commands = base_commands + [
        BotCommand(command="admin", description="لوحة إدارة الأدمن"),
        BotCommand(command="stats", description="إحصائيات البوت (أدمن)"),
        BotCommand(command="broadcast", description="بث رسالة (أدمن)"),
        BotCommand(command="content_status", description="صحة المحتوى (أدمن)"),
        BotCommand(command="errors", description="آخر الأخطاء (أدمن)"),
    ]
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.set_my_commands(
                admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id)
            )
        except Exception as e:
            logger.warning(f"Could not set admin commands for {admin_id}: {e}")

    logger.info("Bot is running!")


async def on_shutdown(bot: Bot, scheduler: BotScheduler):
    logger.info("Shutting down...")
    await scheduler.stop()
    await bot.session.close()
    release_pid_lock()
    logger.info("Bot stopped")


async def main():
    if config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("BOT_TOKEN not set!")
        sys.exit(1)

    acquire_pid_lock()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    scheduler = BotScheduler(bot)

    dp.message.middleware(RateLimitMiddleware(admin_ids=config.ADMIN_IDS))
    dp.callback_query.middleware(RateLimitMiddleware(admin_ids=config.ADMIN_IDS))

    dp.include_router(router)

    logger.info("Starting polling...")
    try:
        await on_startup(bot, scheduler)
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await on_shutdown(bot, scheduler)


if __name__ == "__main__":
    asyncio.run(main())
