"""
Athar Shia Bot - Main Entry Point
بوت أثر الشيعة - نقطة التشغيل الرئيسية

To run:
    python app.py

Required environment variables:
    BOT_TOKEN - Your Telegram Bot Token
"""

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import config
import database as db
from handlers import register_handlers
from scheduler import BotScheduler
from middleware import RateLimitMiddleware

# ─── Logging Setup ───

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)

# ─── PID Lock (prevent multiple instances) ───

PID_FILE = "/tmp/athar_bot.pid"


def acquire_pid_lock():
    """Ensure only one instance of the bot is running."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                old_pid = int(f.read().strip())
            # Check if the old process is still alive
            os.kill(old_pid, 0)
            logger.error(f"❌ Another instance is already running (PID {old_pid}). Killing it...")
            os.kill(old_pid, 9)
            import time
            time.sleep(2)
        except (ValueError, ProcessLookupError, PermissionError):
            pass

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    logger.info(f"✅ PID lock acquired (PID {os.getpid()})")


def release_pid_lock():
    """Remove the PID lock file."""
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            if pid == os.getpid():
                os.remove(PID_FILE)
    except Exception:
        pass


# ─── Bot & Dispatcher ───

storage = MemoryStorage()
bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=storage)

# ─── Scheduler ───

scheduler = BotScheduler(bot)


# ─── Startup & Shutdown ───

async def on_startup(dispatcher):
    """Actions on bot startup."""
    logger.info("🚀 Starting Athar Shia Bot...")

    # Delete any existing webhook to avoid conflicts
    await bot.delete_webhook(drop_pending_updates=False)
    logger.info("✅ Webhook cleared")

    # Initialize database
    db.init_database()
    logger.info("✅ Database initialized")

    # Start scheduler
    await scheduler.start()

    # Set bot commands (global — for all users)
    base_commands = [
        types.BotCommand("start", "بدء البوت وعرض القائمة الرئيسية"),
        types.BotCommand("menu", "القائمة الرئيسية"),
        types.BotCommand("prayer", "مواقيت الصلاة"),
        types.BotCommand("event", "مناسبة اليوم"),
        types.BotCommand("daily", "المحتوى اليومي"),
        types.BotCommand("subs", "إدارة الاشتراكات"),
        types.BotCommand("city", "تغيير المدينة"),
        types.BotCommand("about", "المساعدة والأوامر"),
        types.BotCommand("id", "الحصول على معرفك"),
    ]
    await bot.set_my_commands(base_commands)

    # Set admin-only commands for each admin
    admin_commands = base_commands + [
        types.BotCommand("admin", "لوحة إدارة الأدمن"),
        types.BotCommand("stats", "إحصائيات البوت (أدمن)"),
        types.BotCommand("broadcast", "بث رسالة (أدمن)"),
        types.BotCommand("content_status", "صحة المحتوى (أدمن)"),
        types.BotCommand("errors", "آخر الأخطاء (أدمن)"),
    ]
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.set_my_commands(
                admin_commands,
                scope=types.BotCommandScopeChat(chat_id=admin_id)
            )
        except Exception as e:
            logger.warning(f"Could not set admin commands for {admin_id}: {e}")
    logger.info("✅ Bot commands set")

    logger.info("🟢 Bot is running!")
    logger.info("🤖 @AtharShiaBot")


async def on_shutdown(dispatcher):
    """Actions on bot shutdown."""
    logger.info("🛑 Shutting down...")
    await scheduler.stop()
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()
    await bot.session.close()
    release_pid_lock()
    logger.info("👋 Bot stopped")


# ─── Import types here for commands ───
from aiogram import types


# ─── Main ───

def main():
    """Run the bot."""
    if config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ BOT_TOKEN not set! Please set it in config.py or as environment variable.")
        print("""
╔══════════════════════════════════════════════════════════════╗
║  ❌ BOT_TOKEN غير مضبوط!                                      ║
╠══════════════════════════════════════════════════════════════╣
║  يمكنك ضبط التوكن بإحدى طريقتين:                             ║
║                                                               ║
║  1. متغير بيئة:                                               ║
║     export BOT_TOKEN="your_token_here"                        ║
║                                                               ║
║  2. تعديل ملف config.py:                                      ║
║     BOT_TOKEN = "your_token_here"                             ║
╚══════════════════════════════════════════════════════════════╝
        """)
        sys.exit(1)

    # Acquire PID lock (kills old instance if running)
    acquire_pid_lock()

    # Register rate limit middleware
    dp.middleware.setup(RateLimitMiddleware(admin_ids=config.ADMIN_IDS))
    logger.info("✅ Rate limit middleware registered")

    # Register all handlers
    register_handlers(dp)
    logger.info("✅ Handlers registered")

    # Start polling
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )


if __name__ == "__main__":
    main()
