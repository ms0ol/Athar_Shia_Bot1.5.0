"""
Athar Shia Bot - Scheduler
بوت أثر الشيعة - النظام الزمني
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


async def safe_gather_send(coros: list, batch_size: int = 25, delay: float = 1.0):
    """
    نفّذ قائمة coroutines بإرسال متوازٍ آمن يحترم حدود تيليغرام.

    القواعد المطبّقة:
    • batch_size=25  → أقل من حد تيليغرام (30 رسالة/ثانية)
    • delay=1.0 ثانية بين الدفعات → يضمن عدم تجاوز 25 رسالة/ثانية أبداً
    • return_exceptions=True → فشل رسالة واحدة لا يوقف باقي الدفعة

    يُرجع (sent, failed).
    """
    sent = failed = 0
    total_batches = (len(coros) + batch_size - 1) // batch_size

    for batch_idx, i in enumerate(range(0, len(coros), batch_size)):
        batch = coros[i : i + batch_size]
        results = await asyncio.gather(*batch, return_exceptions=True)

        for r in results:
            if isinstance(r, Exception):
                failed += 1
                logger.warning("safe_gather_send batch=%d/%d error: %s",
                               batch_idx + 1, total_batches, r)
            else:
                sent += 1

        if i + batch_size < len(coros):
            await asyncio.sleep(delay)

    logger.debug("safe_gather_send done: sent=%d failed=%d", sent, failed)
    return sent, failed


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
            asyncio.create_task(self._pre_prayer_reminder_loop()),
            asyncio.create_task(self._daily_content_loop()),
            asyncio.create_task(self._event_check_loop()),
            asyncio.create_task(self._midnight_reset_loop()),
            asyncio.create_task(self._tasbih_reminder_loop()),
            asyncio.create_task(self._weekly_report_loop()),
            asyncio.create_task(self._content_health_loop()),
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

                async def _send_prayer_to_user(user):
                    times = await get_prayer_times(
                        user.get("latitude", config.LATITUDE),
                        user.get("longitude", config.LONGITUDE),
                        user.get("timezone", config.TIMEZONE),
                        user.get("city", config.CITY)
                    )
                    prayer_names = {
                        "fajr": "الفجر 🌅",
                        "dhuhr": "الظهر ☀️",
                        "asr": "العصر 🌤",
                        "maghrib": "المغرب 🌇",
                        "isha": "العشاء 🌙"
                    }
                    for prayer, time_str in times.items():
                        if prayer in ["sunrise", "midnight"]:
                            continue
                        if time_str == current_time:
                            text = (
                                f"🕌 <b>حان وقت صلاة {prayer_names.get(prayer, prayer)}</b>\n\n"
                                f"📍 {user.get('city', config.CITY)}\n"
                                f"🕐 {current_time}\n\n"
                                f"📿 <b>الأذكار المستحبة:</b>\n"
                                f"• تكبيرة الإحرام\n• سورة الحمد\n"
                                f"• سورة الإخلاص (3 مرات)\n"
                                f"• الصلاة على محمد وآل محمد\n"
                                f"• الدعاء بعد الصلاة\n\n"
                                f"<i>قال الإمام الصادق عليه السلام:\n"
                                f"\"مَنْ تَوَضَّأَ وَأَحْسَنَ الوُضُوءَ ثُمَّ صَلَّى رَكْعَتَيْنِ"
                                f" أوْ رَكْعَةً أجَارَهُ اللهُ مِنْ نَارِ جَهَنَّمَ\"</i>\n\n"
                                f"🤲 تقبل الله صلاتكم"
                            )
                            await self.bot.send_message(
                                user["user_id"], text, parse_mode="HTML"
                            )

                coros = [_send_prayer_to_user(u) for u in users]
                if coros:
                    sent, failed = await safe_gather_send(coros)
                    logger.info("[Prayer] إرسال: %d ✅  %d ❌  (من %d مستخدم)",
                                sent, failed, len(users))

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

                        async def _send_content(user, _sub=sub_type, _title=title):
                            content = get_random_content_for_subscription(_sub, user["user_id"])
                            if content:
                                await self.bot.send_message(
                                    user["user_id"],
                                    f"{_title}\n\n{content['text']}",
                                    parse_mode="HTML"
                                )

                        coros = [_send_content(u) for u in users]
                        if coros:
                            sent, failed = await safe_gather_send(coros)
                            logger.info("[Daily:%s] إرسال: %d ✅  %d ❌",
                                        sub_type, sent, failed)

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
                        logger.info(f"[Event] المناسبات اليوم: {len(events)} مناسبة - إرسال لـ {len(users)} مشترك")

                        async def _send_event(user, event):
                            await self.bot.send_message(
                                user["user_id"], format_event(event), parse_mode="HTML"
                            )

                        coros = [
                            _send_event(u, ev)
                            for u in users
                            for ev in events
                        ]
                        sent, failed = await safe_gather_send(coros)
                        logger.info("[Event] إرسال: %d ✅  %d ❌  (من %d مستخدم × %d مناسبة)",
                                    sent, failed, len(users), len(events))
                    else:
                        logger.info("[Event] لا توجد مناسبات لهذا اليوم - لم يتم إرسال أي إشعار")

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
                    users = db.get_all_users()
                    coros = [
                        self.bot.send_message(u["user_id"], text, parse_mode="HTML")
                        for u in users
                    ]
                    if coros:
                        sent, failed = await safe_gather_send(coros)
                        logger.info("[Tasbih] إرسال: %d ✅  %d ❌", sent, failed)

                    await asyncio.sleep(120)

                await asyncio.sleep(55)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in tasbih reminder loop: {e}")
                await asyncio.sleep(60)

    # ─── Pre-Prayer Reminder (15 min before) ───

    async def _pre_prayer_reminder_loop(self):
        """Send reminder 15 minutes before each prayer to subscribed users."""
        while self.running:
            try:
                now = _now()
                future = now + timedelta(minutes=15)
                future_time = f"{future.hour:02d}:{future.minute:02d}"

                users = db.get_subscribed_users("prayer_reminder")

                async def _send_pre_prayer(user, _future_time=future_time):
                    times = await get_prayer_times(
                        user.get("latitude", config.LATITUDE),
                        user.get("longitude", config.LONGITUDE),
                        user.get("timezone", config.TIMEZONE),
                        user.get("city", config.CITY)
                    )
                    prayer_names_ar = {
                        "fajr":    "الفجر 🌅",
                        "dhuhr":   "الظهر ☀️",
                        "asr":     "العصر 🌤",
                        "maghrib": "المغرب 🌇",
                        "isha":    "العشاء 🌙",
                    }
                    for prayer, time_str in times.items():
                        if prayer in ["sunrise", "midnight", "asr"]:
                            continue
                        if time_str == _future_time:
                            text = (
                                f"⏰ <b>تذكير: صلاة {prayer_names_ar.get(prayer, prayer)} بعد 15 دقيقة</b>\n\n"
                                f"📍 {user.get('city', config.CITY)}\n"
                                f"🕐 موعد الصلاة: {time_str}\n\n"
                                f"📿 استعد وأوضأ من الآن\n"
                                f"🤲 الصلاة على محمد وآل محمد"
                            )
                            await self.bot.send_message(
                                user["user_id"], text, parse_mode="HTML"
                            )

                coros = [_send_pre_prayer(u) for u in users]
                if coros:
                    sent, failed = await safe_gather_send(coros)
                    logger.info("[PrePrayer] إرسال: %d ✅  %d ❌", sent, failed)

                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in pre-prayer reminder loop: {e}")
                await asyncio.sleep(60)

    # ─── Weekly Admin Report ───

    async def _weekly_report_loop(self):
        """Send weekly stats report to admin every Sunday at 7:00 AM."""
        while self.running:
            try:
                now = _now()
                if now.weekday() == 6 and now.hour == 7 and now.minute == 0:
                    total = db.get_user_count()
                    new_7d = db.get_new_users_count(7)
                    active_7d = db.get_active_users_count(7)
                    sub_counts = db.get_subscription_counts()
                    db_size = db.get_db_size()

                    sub_text = "\n".join(
                        f"  • {k}: {v}" for k, v in sub_counts.items()
                    ) or "  لا يوجد"

                    text = (
                        f"📊 <b>التقرير الأسبوعي — أثَر | ATHAR</b>\n"
                        f"📅 {now.strftime('%Y-%m-%d')}\n\n"
                        f"👥 <b>المستخدمون:</b>\n"
                        f"  • الإجمالي: {total}\n"
                        f"  • جدد هذا الأسبوع: {new_7d}\n"
                        f"  • نشطون هذا الأسبوع: {active_7d}\n\n"
                        f"🔔 <b>الاشتراكات الفعالة:</b>\n{sub_text}\n\n"
                        f"💾 قاعدة البيانات: {db_size:.1f} KB"
                    )
                    for admin_id in config.ADMIN_IDS:
                        try:
                            await self.bot.send_message(admin_id, text, parse_mode="HTML")
                        except Exception as e:
                            logger.error(f"Weekly report error for admin {admin_id}: {e}")

                    await asyncio.sleep(120)

                await asyncio.sleep(55)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in weekly report loop: {e}")
                await asyncio.sleep(60)

    # ─── Content Health Monitor ───

    async def _content_health_loop(self):
        """Check content files health and notify admin daily at 3:00 AM."""
        while self.running:
            try:
                now = _now()
                if now.hour == 3 and now.minute == 0:
                    from pathlib import Path
                    import json as _json

                    DATA_DIR = Path("data/normalized")
                    files_to_check = [
                        ("daily_content/hadith.json",       "الأحاديث"),
                        ("daily_content/wisdom.json",        "الحكم"),
                        ("daily_content/daily_dua.json",     "الأدعية اليومية"),
                        ("library/munajat.json",             "المناجيات"),
                        ("library/ziyarat.json",             "الزيارات"),
                        ("library/duas.json",                "أدعية المكتبة"),
                        ("event_content/events.json",        "المناسبات"),
                        ("event_content/weekly_duas.json",   "الأدعية الأسبوعية"),
                    ]
                    issues = []
                    for rel_path, label in files_to_check:
                        fpath = DATA_DIR / rel_path
                        if not fpath.exists():
                            issues.append(f"❌ {label}: الملف غير موجود")
                            continue
                        try:
                            with open(fpath, encoding="utf-8") as f:
                                data = _json.load(f)
                            count = len(data.get("items", []))
                            if count == 0:
                                issues.append(f"⚠️ {label}: فارغ (0 عناصر)")
                            elif count < 5:
                                issues.append(f"🔶 {label}: قليل ({count} عناصر)")
                        except Exception as e:
                            issues.append(f"❌ {label}: خطأ في القراءة")

                    if issues:
                        text = "🔍 <b>تقرير صحة المحتوى اليومي</b>\n\n" + "\n".join(issues)
                    else:
                        text = "✅ <b>تقرير صحة المحتوى اليومي</b>\n\nجميع الملفات سليمة."

                    for admin_id in config.ADMIN_IDS:
                        try:
                            await self.bot.send_message(admin_id, text, parse_mode="HTML")
                        except Exception as e:
                            logger.error(f"Content health error for admin {admin_id}: {e}")

                    await asyncio.sleep(120)

                await asyncio.sleep(55)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in content health loop: {e}")
                await asyncio.sleep(60)

    # ─── Manual Trigger (for admin) ───

    async def send_broadcast(self, text: str, admin_only: bool = False):
        """
        إرسال رسالة جماعية بـ asyncio.gather مع حماية حدود تيليغرام.
        25 رسالة/دفعة + انتظار 1 ثانية بين الدفعات = أقصى 25 رسالة/ثانية.
        """
        users = db.get_all_users()
        coros = [
            self.bot.send_message(u["user_id"], text, parse_mode="HTML")
            for u in users
        ]
        sent, failed = await safe_gather_send(coros)
        logger.info("[Broadcast] إرسال: %d ✅  %d ❌  (إجمالي: %d)", sent, failed, len(users))
        return sent, failed
