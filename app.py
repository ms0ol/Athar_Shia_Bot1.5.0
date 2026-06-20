"""
Athar Shia Bot - Main Entry Point
بوت آثار الشيعة - نقطة التشغيل الرئيسية

To run:
    python app.py

Required environment variables:
    BOT_TOKEN - Your Telegram Bot Token
"""

import asyncio
import logging
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

    # Initialize database
    db.init_database()
    logger.info("✅ Database initialized")

    # Start scheduler
    await scheduler.start()

    # Set bot commands
    await bot.set_my_commands([
        types.BotCommand("start", "بدء البوت وعرض القائمة الرئيسية"),
        types.BotCommand("menu", "القائمة الرئيسية"),
        types.BotCommand("prayer", "مواقيت الصلاة"),
        types.BotCommand("event", "مناسبة اليوم"),
        types.BotCommand("daily", "المحتوى اليومي"),
        types.BotCommand("subs", "إدارة الاشتراكات"),
        types.BotCommand("city", "تغيير المدينة"),
        types.BotCommand("about", "حول البوت"),
        types.BotCommand("help", "المساعدة"),
    ])
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
