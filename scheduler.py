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

def chunk_users(users_list, chunk_size=30):
    """تقسيم قائمة المستخدمين إلى مجموعات صغيرة (كل مجموعة 30 مستخدم)"""
    for i in range(0, len(users_list), chunk_size):
        yield users_list[i:i + chunk_size]


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

                # تطبيق فكرتك: تقسيم المستخدمين إلى دفعات (كل دفعة 30 مستخدم)
                for chunk in chunk_users(users, chunk_size=30):
                    for user in chunk:
                        try:
                            times = await get_prayer_times(
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

                    # الانتظار لمدة ثانيتين بعد كل 30 مستخدم كما اقترحت
                    await asyncio.sleep(2)

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
                        logger.info(f"[Event] المناسبات اليوم: {len(events)} مناسبة - إرسال لـ {len(users)} مشترك")

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
                    # Send to all users
                    users = db.get_all_users()

                    # تطبيق فكرتك: تقسيم الإرسال إلى مجموعات بانتظار ثانيتين
                    for chunk in chunk_users(users, chunk_size=30):
                        for user in chunk:
                            try:
                                await self.bot.send_message(user["user_id"], text, parse_mode="HTML")
                            except Exception as e:
                                logger.error(f"Error sending tasbih reminder: {e}")

                        await asyncio.sleep(2) # انتظار ثانيتين

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

                for user in users:
                    try:
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
                            if time_str == future_time:
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
                    except Exception as e:
                        logger.error(f"Pre-prayer reminder error for {user['user_id']}: {e}")

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
        """Send a broadcast message to all users."""
        users = db.get_all_users()
        sent = 0
        failed = 0

        # تطبيق فكرتك لحماية البوت أثناء الإرسال اليدوي الجماعي
        for chunk in chunk_users(users, chunk_size=30):
            for user in chunk:
                try:
                    await self.bot.send_message(user["user_id"], text, parse_mode="HTML")
                    sent += 1
                except Exception as e:
                    logger.error(f"Broadcast failed for {user['user_id']}: {e}")
                    failed += 1

            await asyncio.sleep(2) # انتظار ثانيتين قبل الانتقال لـ 30 مستخدم آخرين

        return sent, failed
