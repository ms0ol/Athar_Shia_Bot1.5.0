"""
handlers/admin.py — أوامر الأدمن والبث والإحصائيات
"""

import logging

from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

import config
import database as db
from services.navigation_service import admin_settings_menu

logger = logging.getLogger(__name__)
router = Router(name="admin_router")


def _is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


# ═══════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not _is_admin(message.from_user.id):
        return

    status = db.get_state("new_user_notifications", "true")
    status_text = "✅ مفعل" if status == "true" else "❌ معطل"
    text = (
        f"🔴 <b>لوحة إدارة الأدمن</b>\n\n"
        f"📊 عدد المستخدمين: {db.get_user_count()}\n"
        f"🔔 تنبيه الأعضاء الجدد: {status_text}\n\n"
        f"اختر من القائمة أدناه:"
    )
    await message.answer(text, reply_markup=admin_settings_menu(), parse_mode="HTML")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not _is_admin(message.from_user.id):
        return

    total = db.get_user_count()
    new_7d = db.get_new_users_count(7)
    new_30d = db.get_new_users_count(30)
    active_7d = db.get_active_users_count(7)
    sub_counts = db.get_subscription_counts()
    db_size = db.get_db_size()

    sub_text = "\n".join(f"  • {k}: {v}" for k, v in sub_counts.items()) or "  لا يوجد"

    text = (
        f"📊 <b>إحصائيات أثَر | ATHAR</b>\n\n"
        f"👥 <b>المستخدمون:</b>\n"
        f"  • الإجمالي: {total}\n"
        f"  • جدد (7 أيام): {new_7d}\n"
        f"  • جدد (30 يوم): {new_30d}\n"
        f"  • نشطون (7 أيام): {active_7d}\n\n"
        f"🔔 <b>الاشتراكات الفعالة:</b>\n{sub_text}\n\n"
        f"💾 قاعدة البيانات: {db_size:.1f} KB"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject):
    if not _is_admin(message.from_user.id):
        return

    args = command.args
    if not args:
        await message.answer(
            "📢 <b>بث رسالة لجميع المستخدمين:</b>\n"
            "<code>/broadcast نص الرسالة</code>\n\n"
            "💡 <b>لإضافة زر وصول سريع لميزة جديدة:</b>\n"
            "<code>/broadcast نص الرسالة | اسم الزر | المعرف</code>\n\n"
            "<b>مثال للتعقيبات:</b>\n"
            "<code>/broadcast أضفنا تحسينات جديدة لقسم التعقيبات! | 📿 عرض التعقيبات | show_feedback</code>",
            parse_mode="HTML"
        )
        return

    text_to_send = args
    reply_markup = None

    if "|" in args:
        parts = args.split("|")
        if len(parts) >= 3:
            text_to_send = parts[0].strip()
            btn_text = parts[1].strip()
            feature_target = parts[2].strip()

            bot_user = await message.bot.get_me()
            deep_link_url = f"https://t.me/{bot_user.username}?start={feature_target}"
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=btn_text, url=deep_link_url)]]
            )

    users = db.get_all_users()
    await message.answer(
        f"📢 جاري الإرسال إلى <b>{len(users)}</b> مستخدم…\n"
        f"<i>(دفعات 25 رسالة/ثانية — آمن من حدود تيليغرام)</i>",
        parse_mode="HTML"
    )

    from scheduler import safe_gather_send
    coros = [
        message.bot.send_message(
            u["user_id"], text_to_send, parse_mode="HTML", reply_markup=reply_markup
        )
        for u in users
    ]
    sent, failed = await safe_gather_send(coros)

    await message.answer(
        f"✅ <b>اكتمل البث</b>\n\n• تم الإرسال: {sent}\n• فشل: {failed}",
        parse_mode="HTML"
    )


@router.message(Command("content_status"))
async def cmd_content_status(message: Message):
    if not _is_admin(message.from_user.id):
        return

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
        ("prayer_content/fajr.json",         "تعقيبات الفجر"),
        ("prayer_content/dhuhr.json",        "تعقيبات الظهر"),
        ("prayer_content/maghrib.json",      "تعقيبات المغرب"),
        ("prayer_content/isha.json",         "تعقيبات العشاء"),
    ]

    lines = ["🔍 <b>حالة ملفات المحتوى</b>\n"]
    for rel_path, label in files_to_check:
        fpath = DATA_DIR / rel_path
        if not fpath.exists():
            lines.append(f"❌ {label}: غير موجود")
            continue
        try:
            with open(fpath, encoding="utf-8") as f:
                data = _json.load(f)
            count = len(data.get("items", []))
            size_kb = fpath.stat().st_size / 1024
            icon = "✅" if count >= 5 else ("🔶" if count > 0 else "⚠️")
            lines.append(f"{icon} {label}: {count} عنصر ({size_kb:.1f} KB)")
        except Exception as e:
            lines.append(f"❌ {label}: خطأ — {e}")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("errors"))
async def cmd_errors(message: Message):
    if not _is_admin(message.from_user.id):
        return

    errors = db.get_error_logs(10)
    if not errors:
        await message.answer("✅ لا توجد أخطاء مسجلة.")
        return

    lines = ["⚠️ <b>آخر 10 أخطاء:</b>\n"]
    for err in errors:
        lines.append(
            f"🔸 {str(err.get('logged_at', ''))[:16]}\n"
            f"   المستخدم: {err.get('user_id', '—')}\n"
            f"   الأمر: {err.get('command', '—')}\n"
            f"   الخطأ: {str(err.get('error_msg', ''))[:100]}\n"
        )
    await message.answer("\n".join(lines), parse_mode="HTML")


# ═══════════════════════════════════════════════════════════
# ADMIN CALLBACK
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin:toggle_new_user")
async def callback_admin_toggle_new_user(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        await call.answer()
        return

    current = db.get_state("new_user_notifications", "true")
    new_state = "false" if current == "true" else "true"
    db.set_state("new_user_notifications", new_state)

    status_text = "✅ مفعل" if new_state == "true" else "❌ معطل"
    text = (
        f"🔴 <b>لوحة إدارة الأدمن</b>\n\n"
        f"📊 عدد المستخدمين: {db.get_user_count()}\n"
        f"🔔 تنبيه الأعضاء الجدد: {status_text}\n\n"
        f"اختر من القائمة أدناه:"
    )
    await call.message.edit_text(text, reply_markup=admin_settings_menu(), parse_mode="HTML")
    await call.answer(f"تم: {status_text}")
