"""
Athar Shia Bot - Scheduler
بوت آثار الشيعة - النظام الزمني
"""

import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot
import pytz

import config
import database as db
from services.content_service import get_random_content_for_subscription
from services.prayer_service import get_prayer_times, get_next_prayer
from services.event_service import get_today_events_list, format_event


def _now() -> datetime:
    """Return current time in the configured timezone."""
    return datetime.now(pytz.timezone(config.TIMEZONE))

logger = logging.getLogger(__name__)


class BotScheduler:
    """Central scheduler for timed tasks."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.running = False
        self.tasks = []

    async def start(self):
        """Start all scheduled tasks."""
        self.running = True
        logger.info("🕐 Starting scheduler...")

        self.tasks = [
            asyncio.create_task(self._prayer_reminder_loop()),
            asyncio.create_task(self._daily_content_loop()),
            asyncio.create_task(self._event_check_loop()),
            asyncio.create_task(self._midnight_reset_loop()),
            asyncio.create_task(self._tasbih_reminder_loop()),
        ]

        logger.info("✅ Scheduler started with %d tasks", len(self.tasks))

    async def stop(self):
        """Stop all scheduled tasks."""
        self.running = False
        for task in self.tasks:
            task.cancel()
        logger.info("🛑 Scheduler stopped")

    # ─── Prayer Reminders ───

    async def _prayer_reminder_loop(self):
        """Send prayer reminders to subscribed users."""
        while self.running:
            try:
                now = _now()
                current_time = f"{now.hour:02d}:{now.minute:02d}"

                # Get all subscribed users
                users = db.get_subscribed_users("prayer_reminder")

                for user in users:
                    try:
                        times = get_prayer_times(
                            user.get("latitude", config.LATITUDE),
                            user.get("longitude", config.LONGITUDE),
                            user.get("timezone", config.TIMEZONE),
                            user.get("city", config.CITY)
                        )

                        # Check if current time matches any prayer time
                        for prayer, time_str in times.items():
                            if prayer in ["sunrise", "midnight"]:
                                continue

                            if time_str == current_time:
                                prayer_names = {
                                    "fajr": "الفجر 🌅",
                                    "dhuhr": "الظهر ☀️",
                                    "asr": "العصر 🌤",
                                    "maghrib": "المغرب 🌇",
                                    "isha": "العشاء 🌙"
                                }

                                text = f"""
🕌 <b>حان وقت صلاة {prayer_names.get(prayer, prayer)}</b>

📍 {user.get('city', config.CITY)}
🕐 {current_time}

📿 <b>الأذكار المستحبة:</b>
• تكبيرة الإحرام
• سورة الحمد
• سورة الإخلاص (3 مرات)
• الصلاة على محمد وآل محمد
• الدعاء بعد الصلاة

<i>قال الإمام الصادق عليه السلام:
"مَنْ تَوَضَّأَ وَأَحْسَنَ الوُضُوءَ ثُمَّ صَلَّى رَكْعَتَيْنِ
أوْ رَكْعَةً أجَارَهُ اللهُ مِنْ نَارِ جَهَنَّمَ يَوْمَ يَقُومُ النَّاسُ لِرَبِّ العَالَمِينَ"</i>

🤲 تقبل الله صلاتكم
"""
                                await self.bot.send_message(
                                    user["user_id"],
                                    text,
                                    parse_mode="HTML"
                                )

                    except Exception as e:
                        logger.error(f"Error sending prayer reminder to {user['user_id']}: {e}")

                # Check every minute
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in prayer reminder loop: {e}")
                await asyncio.sleep(60)

    # ─── Daily Content ───

    async def _daily_content_loop(self):
        """Send daily content to subscribed users at 6 AM."""
        while self.running:
            try:
                now = _now()

                # Send at 6:00 AM
                if now.hour == 6 and now.minute == 0:
                    content_types = {
                        "hadith_daily": "📖 حديث اليوم",
                        "wisdom_daily": "💎 حكمة اليوم",
                        "dua_daily": "🤲 دعاء اليوم",
                        "munajat_daily": "✨ مناجاة اليوم",
                    }

                    for sub_type, title in content_types.items():
                        users = db.get_subscribed_users(sub_type)

                        for user in users:
                            try:
                                content = get_random_content_for_subscription(sub_type, user["user_id"])
                                if content:
                                    text = f"{title}\n\n{content['text']}"
                                    await self.bot.send_message(
                                        user["user_id"],
                                        text,
                                        parse_mode="HTML"
                                    )
                            except Exception as e:
                                logger.error(f"Error sending {sub_type} to {user['user_id']}: {e}")

                    # Wait to avoid duplicate sends
                    await asyncio.sleep(120)

                await asyncio.sleep(55)  # Check every ~minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in daily content loop: {e}")
                await asyncio.sleep(60)

    # ─── Event Check ───

    async def _event_check_loop(self):
        """Check for daily events and notify subscribers."""
        while self.running:
            try:
                now = _now()

                # Check at 5:00 AM
                if now.hour == 5 and now.minute == 0:
                    events = get_today_events_list()

                    if events:
                        users = db.get_subscribed_users("event_reminder")

                        for user in users:
                            for event in events:
                                try:
                                    text = format_event(event)
                                    await self.bot.send_message(
                                        user["user_id"],
                                        text,
                                        parse_mode="HTML"
                                    )
                                except Exception as e:
                                    logger.error(f"Error sending event to {user['user_id']}: {e}")

                    await asyncio.sleep(120)

                await asyncio.sleep(55)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event check loop: {e}")
                await asyncio.sleep(60)

    # ─── Midnight Reset ───

    async def _midnight_reset_loop(self):
        """Reset daily tracking at midnight."""
        while self.running:
            try:
                now = _now()

                if now.hour == 0 and now.minute == 0:
                    db.reset_daily_tracking()
                    logger.info("🌙 Daily content tracking reset")
                    await asyncio.sleep(120)

                await asyncio.sleep(55)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in midnight reset loop: {e}")
                await asyncio.sleep(60)

    # ─── Tasbih Reminder (optional) ───

    async def _tasbih_reminder_loop(self):
        """Send tasbih reminders at specific times."""
        while self.running:
            try:
                now = _now()
                current_time = f"{now.hour:02d}:{now.minute:02d}"

                # Remind at 9 PM for night adhkar
                if current_time == "21:00":
                    text = """
📿 <b>تذكير بالأذكار المسائية</b>

• استغفر الله (100 مرة)
• سبحان الله (100 مرة)
• الحمد لله (100 مرة)
• الله أكبر (100 مرة)
• الصلاة على محمد وآل محمد (100 مرة)
• لا حول ولا قوة إلا بالله (100 مرة)

<i>قال الإمام الصادق عليه السلام:
"مَنْ أَكْثَرَ اسْتِغْفَارَهُ فِي شَعْبَانَ أَخْرَجَهُ اللهُ مِنْ قَبْرِهِ
وَوُجُوهُهُ كَالْقَمَرِ فِي لَيْلَةِ الْبَدْرِ"</i>
"""
                    # Send to all users
                    users = db.get_all_users()
                    for user in users:
                        try:
                            await self.bot.send_message(user["user_id"], text, parse_mode="HTML")
                        except Exception as e:
                            logger.error(f"Error sending tasbih reminder: {e}")

                    await asyncio.sleep(120)

                await asyncio.sleep(55)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in tasbih reminder loop: {e}")
                await asyncio.sleep(60)

    # ─── Manual Trigger (for admin) ───

    async def send_broadcast(self, text: str, admin_only: bool = False):
        """Send a broadcast message to all users."""
        users = db.get_all_users()
        sent = 0
        failed = 0

        for user in users:
            try:
                await self.bot.send_message(user["user_id"], text, parse_mode="HTML")
                sent += 1
            except Exception as e:
                logger.error(f"Broadcast failed for {user['user_id']}: {e}")
                failed += 1

        return sent, failed
