"""
handlers/common.py — الأوامر العامة وقائمة التنقل الرئيسية
/start, /menu, /about, /id + main menu callbacks + settings sub-callbacks
"""

import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery

import config
import database as db
from services.navigation_service import (
    main_menu, ibadat_menu, taqibat_menu, library_menu,
    prayer_menu, events_menu, daily_menu, settings_menu,
    favorites_menu, back_button,
)

logger = logging.getLogger(__name__)
router = Router(name="common_router")


# ═══════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════

@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject):
    """Handle /start command with support for deep linking."""
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    is_new = db.add_user(user_id, username, full_name)

    if is_new and db.get_state("new_user_notifications", "true") == "true":
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        notif_text = (
            f"🔔 <b>مستخدم جديد انضم للبوت!</b>\n\n"
            f"👤 الاسم: {full_name}\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"👀 المعرف: @{username or '—'}\n"
            f"🕐 الوقت: {now}\n"
        )
        for admin_id in config.ADMIN_IDS:
            try:
                await message.bot.send_message(admin_id, notif_text, parse_mode="HTML")
            except Exception:
                pass

    start_args = command.args or ""

    if start_args == "show_feedback":
        await message.answer(
            "📿 <b>تعقيبات الصلاة</b>\n\n"
            "تم تحديث قسم التعقيبات بنجاح! اختر الصلاة لعرض تعقيباتها والتحسينات الجديدة:",
            reply_markup=taqibat_menu(),
            parse_mode="HTML"
        )
        return

    elif start_args == "ziyarat_today":
        from services.event_service import get_weekly_ziyarat
        from handlers.ibadat import _day_works_pdf_msg
        ziyarat = get_weekly_ziyarat()

        if not ziyarat:
            await message.answer("🕌 لا توجد زيارة مخصصة لهذا اليوم حالياً.")
            return

        if ziyarat.get("is_pdf") and ziyarat.get("file_id"):
            try:
                ziyarat_msg = await message.answer_document(
                    document=ziyarat["file_id"],
                    caption=f"🕌 <b>{ziyarat.get('title', 'زيارة اليوم')}</b>\n\nنسألكم الدعاء 🤲",
                    parse_mode="HTML"
                )
                existing = _day_works_pdf_msg.get(user_id, [])
                existing.append(ziyarat_msg.message_id)
                _day_works_pdf_msg[user_id] = existing
            except Exception as e:
                logger.error(f"[ZIYARAT TODAY DEEP LINK] {e}")
                await message.answer("⚠️ ملف الزيارة غير متاح حالياً.")
        elif ziyarat.get("text"):
            text = f"🕌 <b>{ziyarat.get('title', 'زيارة اليوم')}</b>\n\n{ziyarat['text']}"
            await message.answer(
                text[:4000],
                parse_mode="HTML",
                reply_markup=back_button("menu:ibadat")
            )
        else:
            await message.answer("⚠️ لا يوجد محتوى للزيارة.")
        return

    elif start_args == "ibadat":
        await message.answer(
            "العبادات اليومية 🌺",
            reply_markup=ibadat_menu(),
            parse_mode="HTML"
        )
        return

    await message.answer(
        config.WELCOME_MESSAGE,
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer(
        "🏠 <b>القائمة الرئيسية</b>",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


@router.message(Command("about", "help"))
async def cmd_about(message: Message):
    is_admin = message.from_user.id in config.ADMIN_IDS

    text = (
        "💡 <b>المساعدة — أثَر | ATHAR</b>\n\n"
        "🔹 <b>الأوامر العامة:</b>\n"
        "  /start — بدء البوت\n"
        "  /menu — القائمة الرئيسية\n"
        "  /prayer — مواقيت الصلاة\n"
        "  /event — مناسبة اليوم\n"
        "  /daily — المحتوى اليومي\n"
        "  /subs — إدارة الاشتراكات\n"
        "  /city المدينة — تغيير المدينة\n"
        "  /id — الحصول على معرفك\n"
        "  /about — معلومات عن البوت\n\n"
    )

    if is_admin:
        text += (
            "🔴 <b>أوامر الأدمن (للأدمن فقط):</b>\n"
            "  /admin — لوحة الإدارة\n"
            "  /stats — إحصائيات البوت\n"
            "  /broadcast النص — بث رسالة للجميع\n"
            "  /content_status — تقرير صحة المحتوى\n"
            "  /errors — آخر الأخطاء\n\n"
        )

    text += (
        "🎨 الميزات الرئيسية:\n"
        "• ⭐ نظام مفضلات لحفظ المحتوى\n"
        "• ⏰ تذكير ما قبل الصلاة بـ 15 دقيقة\n"
        "• 🛡️ حماية من الإساءة والإغراق\n"
        "• 📅 تقرير أسبوعي للأدمن\n"
        "• 🔍 مراقبة صحة المحتوى يومياً"
    )

    await message.answer(text, parse_mode="HTML")


@router.message(Command("id", "myid"))
async def cmd_id(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "—"
    first_name = message.from_user.first_name or "—"
    await message.answer(
        f"💼 <b>معلوماتك في تليجرام</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 الاسم: {first_name}\n"
        f"👀 المعرف: @{username}\n\n"
        f"للاشتراكي: <code>{user_id}</code>",
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════
# MAIN MENU CALLBACKS
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "menu:main")
async def callback_main_menu(call: CallbackQuery):
    from handlers.ibadat import _cleanup_day_works_pdfs
    await _cleanup_day_works_pdfs(call.from_user.id, call.bot)
    await call.message.edit_text(
        "🏠 <b>القائمة الرئيسية</b>\n\nاختر من القائمة:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "menu:ibadat")
async def callback_ibadat(call: CallbackQuery):
    from handlers.ibadat import _cleanup_day_works_pdfs
    await _cleanup_day_works_pdfs(call.from_user.id, call.bot)
    await call.message.edit_text(
        "📿 <b>العبادات اليومية</b>\n\nاختر ما تريد:",
        reply_markup=ibadat_menu(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "menu:library")
async def callback_library(call: CallbackQuery):
    await call.message.edit_text(
        "📚 <b>المكتبة الدينية</b>\n\nالمحتوى الشامل للعبادات:",
        reply_markup=library_menu(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "menu:prayer")
async def callback_prayer(call: CallbackQuery):
    await call.message.edit_text(
        "🕌 <b>الصلاة والأذان</b>\n\nاختر ما تريد:",
        reply_markup=prayer_menu(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "menu:events")
async def callback_events(call: CallbackQuery):
    await call.message.edit_text(
        "🗓 <b>المناسبات والأعمال</b>\n\nاختر ما تريد:",
        reply_markup=events_menu(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "menu:daily")
async def callback_daily(call: CallbackQuery):
    await call.message.edit_text(
        "✨ <b>المحتوى اليومي</b>\n\nاختر ما تريد:",
        reply_markup=daily_menu(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "menu:settings")
async def callback_settings(call: CallbackQuery):
    await call.message.edit_text(
        "⚙️ <b>إعداداتي</b>\n\nاختر ما تريد تعديله:",
        reply_markup=settings_menu(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "menu:favorites")
async def callback_favorites_menu_entry(call: CallbackQuery):
    count = db.get_favorites_count(call.from_user.id)
    text = (
        f"⭐ <b>مفضلاتي</b>\n\n"
        f"لديك <b>{count}</b> عنصر محفوظ.\n"
        "اختر النوع لعرض المحفوظات:"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=favorites_menu())
    await call.answer()


@router.callback_query(F.data == "settings:timezone")
async def callback_settings_timezone(call: CallbackQuery):
    text = (
        "🕐 <b>المنطقة الزمنية</b>\n\n"
        "المنطقة الحالية: Asia/Baghdad (UTC+3)\n\n"
        "يمكنك تغييرها لاحقاً عبر الأمر:\n"
        "<code>/timezone المنطقة</code>"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:settings"))
    await call.answer()


@router.callback_query(F.data == "settings:about")
async def callback_settings_about(call: CallbackQuery):
    await call.message.edit_text(
        config.ABOUT_MESSAGE,
        parse_mode="HTML",
        reply_markup=back_button("menu:settings")
    )
    await call.answer()
