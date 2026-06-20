"""
Athar Shia Bot - Handlers
بوت أثر الشيعة - معالجات الأوامر والأزرار
"""

import asyncio
import logging
import random
from aiogram import types, Dispatcher
from aiogram.types import (
    CallbackQuery, Message,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.utils.exceptions import WrongFileIdentifier, BadRequest

import config
import database as db
from services.content_service import (
    get_random_item, get_daily_content, get_content_by_id,
    format_hadith, format_wisdom, format_dua, format_munajat, format_ziyarat,
    get_random_content_for_subscription, get_all_items
)
from services.prayer_service import (
    get_prayer_times, get_next_prayer, format_prayer_times,
    format_next_prayer, get_prayer_taqibat, format_taqibat
)
from services.event_service import (
    get_today_event, get_upcoming_events, get_weekly_dua,
    get_today_hijri, format_hijri_date, format_event,
    format_upcoming_events, format_weekly_dua, get_hijri_calendar
)
from services.subscription_service import (
    get_subscription_list, toggle_subscription, format_subscriptions_list
)
from services.navigation_service import (
    main_menu, ibadat_menu, taqibat_menu,
    library_menu, library_duas_menu, library_ziyarat_menu, library_munajat_menu,
    prayer_menu, events_menu, daily_menu, settings_menu,
    subscriptions_settings_menu, back_button, pagination_buttons,
    favorites_menu, content_actions_keyboard, make_button,
)

# ═══════════════════════════════════════════════════════════
# PDF DUA HELPER
# ═══════════════════════════════════════════════════════════

async def _send_dua_pdf(call: CallbackQuery, item: dict) -> bool:
    """
    Send a PDF dua document. Checks DB override first, falls back to JSON file_id.
    Returns True on success, False on failure (with user-friendly error shown).
    """
    dua_id = item.get("id", "")
    title = item.get("title", "دعاء يومي")
    caption = f"📿 <b>{title}</b>\n\nنسألكم الدعاء 🤲"

    file_id = db.get_dua_file_id(dua_id) or item.get("file_id")

    try:
        await call.message.answer_document(
            document=file_id,
            caption=caption,
            parse_mode="HTML"
        )
        await call.answer("تم إرسال ملف الدعاء ✅")
        return True
    except (WrongFileIdentifier, BadRequest) as e:
        logging.error(f"[DUA PDF] فشل إرسال {dua_id} ({title}): {e}")
        await call.answer(
            f"⚠️ ملف '{title}' غير متاح حالياً.\n"
            "يرجى إخبار المشرف لتحديث الملف عبر أمر /duas_status",
            show_alert=True
        )
        return False


# ═══════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════
async def cmd_start(message: Message):
    """Handle /start command."""
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    # Register user
    db.add_user(user_id, username, full_name)

    await message.answer(
        config.WELCOME_MESSAGE,
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


async def cmd_menu(message: Message):
    """Handle /menu command."""
    await message.answer(
        "🏠 <b>القائمة الرئيسية</b>",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


async def cmd_prayer(message: Message):
    """Handle /prayer command."""
    await send_prayer_times(message)


async def cmd_event(message: Message):
    """Handle /event command."""
    event = get_today_event()
    if event:
        await message.answer(format_event(event), parse_mode="HTML")
    else:
        await message.answer("📅 لا توجد مناسبة خاصة اليوم.")


async def cmd_daily(message: Message):
    """Handle /daily command."""
    await message.answer(
        "✨ <b>اختر المحتوى اليومي:</b>",
        reply_markup=daily_menu(),
        parse_mode="HTML"
    )


async def cmd_subs(message: Message):
    """Handle /subs command."""
    await show_subscriptions(message)


async def cmd_about(message: Message):
    """Handle /about command."""
    await message.answer(config.ABOUT_MESSAGE, parse_mode="HTML")


# ═══════════════════════════════════════════════════════════
# CALLBACK HANDLERS - MAIN MENU
# ═══════════════════════════════════════════════════════════

async def callback_main_menu(call: CallbackQuery):
    """Handle main menu callback."""
    await call.message.edit_text(
        "🏠 <b>القائمة الرئيسية</b>\n\nاختر من القائمة:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await call.answer()


async def callback_ibadat(call: CallbackQuery):
    """Handle ibadat menu."""
    await call.message.edit_text(
        "📿 <b>العبادات اليومية</b>\n\nاختر ما تريد:",
        reply_markup=ibadat_menu(),
        parse_mode="HTML"
    )
    await call.answer()


async def callback_library(call: CallbackQuery):
    """Handle library menu."""
    await call.message.edit_text(
        "📚 <b>المكتبة الدينية</b>\n\nالمحتوى الشامل للعبادات:",
        reply_markup=library_menu(),
        parse_mode="HTML"
    )
    await call.answer()


async def callback_prayer(call: CallbackQuery):
    """Handle prayer menu."""
    await call.message.edit_text(
        "🕌 <b>الصلاة والأذان</b>\n\nاختر ما تريد:",
        reply_markup=prayer_menu(),
        parse_mode="HTML"
    )
    await call.answer()


async def callback_events(call: CallbackQuery):
    """Handle events menu."""
    await call.message.edit_text(
        "🗓 <b>المناسبات والأعمال</b>\n\nاختر ما تريد:",
        reply_markup=events_menu(),
        parse_mode="HTML"
    )
    await call.answer()


async def callback_daily(call: CallbackQuery):
    """Handle daily content menu."""
    await call.message.edit_text(
        "✨ <b>المحتوى اليومي</b>\n\nاختر ما تريد:",
        reply_markup=daily_menu(),
        parse_mode="HTML"
    )
    await call.answer()


async def callback_settings(call: CallbackQuery):
    """Handle settings menu."""
    await call.message.edit_text(
        "⚙️ <b>إعداداتي</b>\n\nاختر ما تريد تعديله:",
        reply_markup=settings_menu(),
        parse_mode="HTML"
    )
    await call.answer()


# ═══════════════════════════════════════════════════════════
# IBADAT HANDLERS
# ═══════════════════════════════════════════════════════════

async def callback_ibadat_day_works(call: CallbackQuery):
    """Handle day works."""
    hijri = get_today_hijri()
    dua = get_weekly_dua()

    text = f"📅 <b>أعمال اليوم</b>\n"
    text += f"📆 {format_hijri_date(hijri)}\n\n"

    event = get_today_event()
    if event:
        text += f"🎯 <b>مناسبة اليوم:</b> {event.get('title', '')}\n"
        if event.get("amal"):
            text += f"\n✨ <b>الأعمال:</b>\n{event['amal']}\n\n"

    if dua:
        text += f"🤲 <b>دعاء اليوم:</b> {dua.get('title', '')}\n"
        dua_text = dua.get('text', '')
        if dua_text:
            text += f"{dua_text}\n\n"
        else:
            text += "اضغط على <b>دعاء اليوم</b> في القائمة لتحميل الدعاء كاملاً.\n\n"

    text += "📿 تذكر: الصلاة على محمد وآل محمد في كل أحوالك 🌹"

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:ibadat"))
    await call.answer()


async def callback_ibadat_night_works(call: CallbackQuery):
    """Handle night works."""
    hijri = get_today_hijri()

    text = f"🌙 <b>أعمال الليلة</b>\n"
    text += f"📆 {format_hijri_date(hijri)}\n\n"

    text += """
🌟 <b>من المستحبات:</b>

• صلاة الليل (التهجد)
• قراءة سورة الملك
• قراءة سورة السجدة
• الدعاء قبل النوم
• الاستغفار 100 مرة
• الصلاة على محمد وآل محمد 100 مرة
• الدعاء بالمأثورات

🤲 <i>اللهم بحق محمد وعلي وفاطمة والحسن والحسين
علي ومحمد وجعفر وموسى وعلي ومحمد وعلي والحسن
والمهدي اجعلنا من المقبولين</i>
"""
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:ibadat"))
    await call.answer()


async def callback_ibadat_dua_today(call: CallbackQuery):
    """Handle today's dua supporting both text and PDF formats."""
    dua = get_weekly_dua()

    if not dua:
        dua = get_random_item("daily_dua", call.from_user.id)

    if not dua:
        await call.answer("🤲 عذراً، لم يتم العثور على دعاء حالياً.", show_alert=True)
        return

    if dua.get("is_pdf") and dua.get("file_id"):
        await _send_dua_pdf(call, dua)
    elif dua.get("text"):
        text = format_weekly_dua(dua) if dua.get("weekday") else format_dua(dua)
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:ibadat"))
        await call.answer()
    else:
        await call.answer("⚠️ خطأ في بيانات الدعاء.", show_alert=True)


async def callback_ibadat_taqibat(call: CallbackQuery):
    """Handle taqibat submenu."""
    await call.message.edit_text(
        "📿 <b>تعقيبات الصلاة</b>\n\nاختر الصلاة:",
        reply_markup=taqibat_menu(),
        parse_mode="HTML"
    )
    await call.answer()


async def callback_ibadat_what_to_read(call: CallbackQuery):
    """Handle what to read suggestion."""
    user_id = call.from_user.id
    options = ["hadith", "wisdom_short", "munajat", "daily_dua"]
    choice = random.choice(options)

    item = get_random_item(choice, user_id)
    if not item:
        await call.answer("لا يوجد محتوى متوفر حالياً.", show_alert=True)
        return

    db.mark_content_sent(user_id, choice, item["id"])

    if choice == "daily_dua" and item.get("is_pdf") and item.get("file_id"):
        await _send_dua_pdf(call, item)
        return

    formatters = {
        "hadith": format_hadith,
        "wisdom_short": format_wisdom,
        "munajat": format_munajat,
        "daily_dua": format_dua,
    }

    text = formatters[choice](item)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:ibadat"))
    await call.answer("✨ مقترح خاص لك!")


# ═══════════════════════════════════════════════════════════
# TAQIBAT HANDLERS
# ═══════════════════════════════════════════════════════════

prayer_names = {
    "fajr": "الفجر", "dhuhr": "الظهر",
    "maghrib": "المغرب", "isha": "العشاء"
}


async def callback_taqibat(call: CallbackQuery):
    """Handle taqibat for specific prayer."""
    prayer = call.data.split(":")[1]
    data = get_prayer_taqibat(prayer)

    if data:
        text = format_taqibat(data, prayer_names.get(prayer, prayer))
    else:
        text = f"📿 <b>تعقيبات صلاة {prayer_names.get(prayer, prayer)}</b>\n\n"
        text += "سيتم إضافة المحتوى قريباً إن شاء الله."

    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:ibadat"))
    except Exception:
        # If edit fails (e.g. message too long after all), send a new message
        await call.message.answer(text, parse_mode="HTML", reply_markup=back_button("menu:ibadat"))
    await call.answer()


# ═══════════════════════════════════════════════════════════
# LIBRARY HANDLERS
# ═══════════════════════════════════════════════════════════

async def callback_library_duas(call: CallbackQuery):
    """Handle duas in library."""
    items = get_all_items("daily_dua")

    if items:
        kb = pagination_buttons(items, "dua_lib", page=0, per_page=5)
    else:
        kb = library_duas_menu()

    await call.message.edit_text(
        "🤲 <b>الأدعية</b>\n\nاختر دعاء أو اضغط عشوائي:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()


async def callback_library_ziyarat(call: CallbackQuery):
    """Handle ziyarat in library."""
    items = get_all_items("ziyarat")

    if items:
        kb = pagination_buttons(items, "ziyarat_lib", page=0, per_page=5)
    else:
        kb = library_ziyarat_menu()

    await call.message.edit_text(
        "🕌 <b>الزيارات</b>\n\nاختر زيارة أو اضغط عشوائي:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()


async def callback_library_munajat(call: CallbackQuery):
    """Handle munajat in library."""
    items = get_all_items("munajat")

    if items:
        kb = pagination_buttons(items, "munajat_lib", page=0, per_page=5)
    else:
        kb = library_munajat_menu()

    await call.message.edit_text(
        "✨ <b>المناجيات</b>\n\nاختر مناجاة أو اضغط عشوائي:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()


async def callback_library_hadith(call: CallbackQuery):
    """Handle hadith in library."""
    items = get_all_items("hadith")

    if items:
        kb = pagination_buttons(items, "hadith_lib", page=0, per_page=5)
    else:
        kb = back_button("menu:library")

    await call.message.edit_text(
        "📖 <b>الأحاديث</b>\n\nاختر حديثاً:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()


async def callback_library_wisdom(call: CallbackQuery):
    """Handle wisdom in library."""
    items = get_all_items("wisdom_featured")
    if not items:
        items = get_all_items("wisdom_short")

    if items:
        kb = pagination_buttons(items, "wisdom_lib", page=0, per_page=5)
    else:
        kb = back_button("menu:library")

    await call.message.edit_text(
        "💎 <b>الحكم</b>\n\nاختر حكمة:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()


# ═══════════════════════════════════════════════════════════
# RANDOM CONTENT HANDLERS
# ═══════════════════════════════════════════════════════════

async def callback_random_dua(call: CallbackQuery):
    """Handle random dua supporting both text and PDF formats."""
    user_id = call.from_user.id
    item = get_random_item("daily_dua", user_id)

    if not item:
        await call.answer("🤲 عذراً، لم يتم العثور على أدعية متوفرة حالياً.", show_alert=True)
        return

    db.mark_content_sent(user_id, "daily_dua", item["id"])

    if item.get("is_pdf") and item.get("file_id"):
        await _send_dua_pdf(call, item)
    elif item.get("text"):
        await call.message.edit_text(
            format_dua(item), parse_mode="HTML",
            reply_markup=back_button("menu:library")
        )
        await call.answer()
    else:
        await call.answer("⚠️ خطأ في بيانات الدعاء.", show_alert=True)


async def callback_random_ziyarat(call: CallbackQuery):
    """Handle random ziyarat."""
    item = get_random_item("ziyarat", call.from_user.id)
    if item:
        db.mark_content_sent(call.from_user.id, "ziyarat", item["id"])
        text = format_ziyarat(item)
    else:
        text = "🕌 لا يوجد محتوى متوفر حالياً."

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:library"))
    await call.answer()


async def callback_random_munajat(call: CallbackQuery):
    """Handle random munajat."""
    item = get_random_item("munajat", call.from_user.id)
    if item:
        db.mark_content_sent(call.from_user.id, "munajat", item["id"])
        text = format_munajat(item)
    else:
        text = "✨ لا يوجد محتوى متوفر حالياً."

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:library"))
    await call.answer()


# ═══════════════════════════════════════════════════════════
# PRAYER HANDLERS
# ═══════════════════════════════════════════════════════════

async def send_prayer_times(message_or_call):
    """Send prayer times."""
    user = db.get_user(message_or_call.from_user.id)
    if user:
        times = get_prayer_times(
            user.get("latitude", config.LATITUDE),
            user.get("longitude", config.LONGITUDE),
            user.get("timezone", config.TIMEZONE),
            user.get("city", config.CITY)
        )
    else:
        times = get_prayer_times(config.LATITUDE, config.LONGITUDE, config.TIMEZONE, config.CITY)

    text = format_prayer_times(times, user.get("city", config.CITY) if user else config.CITY)

    if isinstance(message_or_call, CallbackQuery):
        await message_or_call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:prayer"))
        await message_or_call.answer()
    else:
        await message_or_call.answer(text, parse_mode="HTML")


async def callback_prayer_times(call: CallbackQuery):
    """Handle prayer times callback."""
    await send_prayer_times(call)


async def callback_prayer_next(call: CallbackQuery):
    """Handle next prayer callback."""
    user = db.get_user(call.from_user.id)
    if user:
        info = get_next_prayer(
            user.get("latitude", config.LATITUDE),
            user.get("longitude", config.LONGITUDE),
            user.get("timezone", config.TIMEZONE),
            user.get("city", config.CITY)
        )
    else:
        info = get_next_prayer(config.LATITUDE, config.LONGITUDE, config.TIMEZONE, config.CITY)

    text = format_next_prayer(info)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:prayer"))
    await call.answer()


async def callback_prayer_taqibat(call: CallbackQuery):
    """Handle prayer taqibat."""
    await call.message.edit_text(
        "📿 <b>تعقيبات الصلاة</b>\n\nاختر الصلاة:",
        reply_markup=taqibat_menu(),
        parse_mode="HTML"
    )
    await call.answer()


async def callback_prayer_reminder(call: CallbackQuery):
    """Handle prayer reminder settings."""
    text = """
🔔 <b>تذكير الصلاة</b>

يمكنك تفعيل تذكير الصلاة من خلال:
الإعدادات ➜ اشتراكاتي ➜ تذكير الصلاة

سيصلك إشعار عند دخول وقت كل صلاة
مع الأذكار والتعقيبات المستحبة.
"""
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:settings"))
    await call.answer()


# ═══════════════════════════════════════════════════════════
# EVENTS HANDLERS
# ═══════════════════════════════════════════════════════════

async def callback_event_today(call: CallbackQuery):
    """Handle today's event."""
    event = get_today_event()
    if event:
        text = format_event(event)
    else:
        hijri = get_today_hijri()
        text = f"📅 <b>مناسبة اليوم</b>\n\n"
        text += f"📆 {format_hijri_date(hijri)}\n\n"
        text += "لا توجد مناسبة خاصة بهذا اليوم.\n\n"
        text += "تفقد المناسبات القادمة من القائمة. 🌹"

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:events"))
    await call.answer()


async def callback_event_upcoming(call: CallbackQuery):
    """Handle upcoming events."""
    events = get_upcoming_events(days=30)
    text = format_upcoming_events(events)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:events"))
    await call.answer()


async def callback_event_works(call: CallbackQuery):
    """Handle event works."""
    event = get_today_event()
    if event and event.get("amal"):
        text = f"✨ <b>أعمال {event.get('title', 'المناسبة')}</b>\n\n"
        text += event["amal"]
    else:
        text = """
✨ <b>أعمال المناسبة</b>

من الأعمال المستحبة بشكل عام:

• الصيام
• الصلاة على محمد وآل محمد
• الدعاء بالمأثورات
• زيارة الإمام الحسين عليه السلام
• قراءة القرآن الكريم
• الصدقة
• الاستغفار

📅 تفقد مناسبة اليوم لمعرفة الأعمال الخاصة بها.
"""
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:events"))
    await call.answer()


async def callback_event_calendar(call: CallbackQuery):
    """Handle Hijri calendar."""
    text = get_hijri_calendar()
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:events"))
    await call.answer()


# ═══════════════════════════════════════════════════════════
# DAILY CONTENT HANDLERS
# ═══════════════════════════════════════════════════════════

async def callback_daily_hadith(call: CallbackQuery):
    """Handle daily hadith."""
    item = get_random_item("hadith", call.from_user.id)
    if item:
        db.mark_content_sent(call.from_user.id, "hadith", item["id"])
        text = format_hadith(item)
    else:
        text = "📖 لا يوجد محتوى متوفر حالياً."

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:daily"))
    await call.answer()


async def callback_daily_wisdom(call: CallbackQuery):
    """Handle daily wisdom."""
    item = get_random_item("wisdom_featured", call.from_user.id)
    if not item:
        item = get_random_item("wisdom", call.from_user.id)

    if item:
        db.mark_content_sent(call.from_user.id, "wisdom", item["id"])
        text = format_wisdom(item)
    else:
        text = "💎 لا يوجد محتوى متوفر حالياً."

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:daily"))
    await call.answer()


async def callback_daily_dua(call: CallbackQuery):
    """Handle daily dua supporting both text and PDF formats."""
    user_id = call.from_user.id
    item = get_random_item("daily_dua", user_id)

    if not item:
        await call.answer("🤲 عذراً، لم يتم العثور على أدعية متوفرة حالياً.", show_alert=True)
        return

    db.mark_content_sent(user_id, "daily_dua", item["id"])

    if item.get("is_pdf") and item.get("file_id"):
        await _send_dua_pdf(call, item)
    elif item.get("text"):
        await call.message.edit_text(
            format_dua(item), parse_mode="HTML",
            reply_markup=back_button("menu:daily")
        )
        await call.answer()
    else:
        await call.answer("⚠️ خطأ في بيانات الدعاء.", show_alert=True)


async def callback_daily_munajat(call: CallbackQuery):
    """Handle daily munajat."""
    item = get_random_item("munajat", call.from_user.id)
    if item:
        db.mark_content_sent(call.from_user.id, "munajat", item["id"])
        text = format_munajat(item)
    else:
        text = "✨ لا يوجد محتوى متوفر حالياً."

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:daily"))
    await call.answer()


async def callback_daily_random(call: CallbackQuery):
    """Handle random daily content — sends ONE randomly chosen item."""
    user_id = call.from_user.id

    options = [
        ("hadith",      format_hadith),
        ("wisdom",      format_wisdom),
        ("daily_dua",   format_dua),
        ("munajat",     format_munajat),
    ]
    random.shuffle(options)

    item = None
    formatter = None
    chosen_type = None

    for content_type, fmt in options:
        item = get_random_item(content_type, user_id)
        if item:
            formatter = fmt
            chosen_type = content_type
            db.mark_content_sent(user_id, content_type, item["id"])
            break

    if not item:
        await call.answer("لا يوجد محتوى متوفر حالياً.", show_alert=True)
        return

    if chosen_type == "daily_dua" and item.get("is_pdf") and item.get("file_id"):
        await _send_dua_pdf(call, item)
        return

    text = formatter(item)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:daily"))
    await call.answer("✨ تم إرسال المحتوى العشوائي!")


# ═══════════════════════════════════════════════════════════
# SETTINGS HANDLERS
# ═══════════════════════════════════════════════════════════

async def show_subscriptions(message_or_call):
    """Show subscriptions."""
    user_id = message_or_call.from_user.id
    subs = get_subscription_list(user_id)
    text = format_subscriptions_list(subs)

    if isinstance(message_or_call, CallbackQuery):
        await message_or_call.message.edit_text(
            text, parse_mode="HTML",
            reply_markup=subscriptions_settings_menu(
                {s["key"]: s["is_active"] for s in subs}
            )
        )
        await message_or_call.answer()
    else:
        await message_or_call.answer(
            text, parse_mode="HTML",
            reply_markup=subscriptions_settings_menu(
                {s["key"]: s["is_active"] for s in subs}
            )
        )


async def callback_settings_subs(call: CallbackQuery):
    """Handle subscriptions settings."""
    await show_subscriptions(call)


async def callback_toggle_subscription(call: CallbackQuery):
    """Handle subscription toggle."""
    sub_key = call.data.split(":")[1]
    new_state = toggle_subscription(call.from_user.id, sub_key)

    subs = get_subscription_list(call.from_user.id)
    text = format_subscriptions_list(subs)

    await call.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=subscriptions_settings_menu(
            {s["key"]: s["is_active"] for s in subs}
        )
    )
    await call.answer("✅ تم" if new_state else "❌ تم الإلغاء")


async def callback_settings_city(call: CallbackQuery):
    """Handle city settings."""
    text = """
🕌 <b>تغيير المدينة</b>

حالياً البوت يستخدم إحداثيات بغداد كافتراضي.

لتغيير المدينة، أرسل الأمر:
<code>/city اسم_المدينة</code>

مثال:
<code>/city كربلاء</code>
<code>/city النجف</code>
<code>/city طهران</code>
"""
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:settings"))
    await call.answer()


async def cmd_city(message: Message):
    """Handle /city command."""
    args = message.get_args()
    if not args:
        await message.answer(
            "🕌 أرسل اسم المدينة:\n<code>/city اسم_المدينة</code>",
            parse_mode="HTML"
        )
        return

    city_name = args.strip()
    # Default coordinates for common cities
    city_coords = {
        # العراق
        "بغداد":               (33.3152, 44.3661),
        "كربلاء":              (32.6160, 44.0248),
        "كربلاء المقدسة":     (32.6160, 44.0248),
        "النجف":               (31.9924, 44.3140),
        "النجف الأشرف":       (31.9924, 44.3140),
        "بصرة":                (30.5156, 47.7804),
        "البصرة":              (30.5156, 47.7804),
        "سامراء":              (34.2009, 43.8738),
        "كاظمية":              (33.3791, 44.3368),
        "الكاظمية":            (33.3791, 44.3368),
        "الكوت":               (32.5000, 45.8167),
        "ديالى":               (33.7665, 44.6441),
        "بعقوبة":              (33.7665, 44.6441),
        "الموصل":              (36.3350, 43.1189),
        "موصل":                (36.3350, 43.1189),
        "أربيل":               (36.1901, 44.0091),
        "السليمانية":          (35.5572, 45.4350),
        "كركوك":               (35.4681, 44.3922),
        "الناصرية":            (31.0543, 46.2594),
        "العمارة":             (31.8394, 47.1547),
        "الحلة":               (32.4757, 44.4422),
        "الديوانية":           (31.9942, 44.9166),
        "الرمادي":             (33.4252, 43.3010),
        "الفلوجة":             (33.3534, 43.7823),
        "تكريت":               (34.5958, 43.6833),
        "الحويجة":             (35.3597, 43.7442),
        "طوزخورماتو":          (34.8764, 44.6333),
        "زاخو":                (37.1444, 42.6825),
        "دهوك":                (36.8669, 43.0035),
        "هيت":                 (33.6453, 42.8272),
        "عنه":                 (34.3699, 41.9869),
        "الرطبة":              (33.0581, 40.2849),
        "القائم":              (34.3791, 41.1084),
        # إيران
        "طهران":               (35.6892, 51.3890),
        "قم":                  (34.6401, 50.8764),
        "مشهد":                (36.2605, 59.6168),
        "أصفهان":              (32.6539, 51.6660),
        "اصفهان":              (32.6539, 51.6660),
        "شيراز":               (29.5926, 52.5836),
        "تبريز":               (38.0800, 46.2919),
        "اهواز":               (31.3183, 48.6706),
        "الأهواز":             (31.3183, 48.6706),
        # المملكة العربية السعودية
        "مكة":                 (21.3891, 39.8579),
        "مكة المكرمة":         (21.3891, 39.8579),
        "المدينة":             (24.5247, 39.5692),
        "المدينة المنورة":     (24.5247, 39.5692),
        "الرياض":              (24.6877, 46.7219),
        "جدة":                 (21.4858, 39.1925),
        "الدمام":              (26.4207, 50.0888),
        "القطيف":              (26.5296, 50.0055),
        # الكويت
        "الكويت":              (29.3759, 47.9774),
        "مدينة الكويت":        (29.3759, 47.9774),
        # البحرين
        "المنامة":             (26.2154, 50.5832),
        # لبنان
        "بيروت":               (33.8938, 35.5018),
        # سوريا
        "دمشق":                (33.5138, 36.2765),
    }

    coords = city_coords.get(city_name)
    if not coords:
        await message.answer(
            f"⚠️ المدينة <b>{city_name}</b> غير موجودة في قاموس المدن.\n\n"
            f"المدن المتاحة:\n"
            f"<b>العراق:</b> بغداد، كربلاء، النجف، بصرة، الكوت، سامراء، كاظمية، الموصل، الناصرية، الحلة، ديالى...\n"
            f"<b>إيران:</b> طهران، قم، مشهد، أصفهان، شيراز...\n"
            f"<b>السعودية:</b> مكة، المدينة، الرياض، جدة، الدمام...\n\n"
            f"مثال: <code>/city الكوت</code>",
            parse_mode="HTML"
        )
        return
    db.update_user_location(message.from_user.id, city_name, coords[0], coords[1])

    await message.answer(
        f"✅ تم تعيين المدينة إلى: <b>{city_name}</b>\n"
        f"📍 الإحداثيات: {coords[0]:.4f}, {coords[1]:.4f}",
        parse_mode="HTML"
    )


async def callback_settings_timezone(call: CallbackQuery):
    """Handle timezone settings."""
    text = """
🕐 <b>المنطقة الزمنية</b>

المنطقة الحالية: Asia/Baghdad (UTC+3)

يمكنك تغييرها لاحقاً عبر الأمر:
<code>/timezone المنطقة</code>
"""
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:settings"))
    await call.answer()


async def callback_settings_about(call: CallbackQuery):
    """Handle about callback."""
    await call.message.edit_text(config.ABOUT_MESSAGE, parse_mode="HTML", reply_markup=back_button("menu:settings"))
    await call.answer()


# ═══════════════════════════════════════════════════════════
# PAGINATION HANDLERS
# ═══════════════════════════════════════════════════════════

async def callback_pagination(call: CallbackQuery):
    """Handle pagination callbacks."""
    parts = call.data.split(":")
    prefix = parts[0]
    action = parts[1]

    if action == "page":
        page = int(parts[2])

        # Map prefix to content type
        content_map = {
            "dua_lib": "daily_dua",
            "ziyarat_lib": "ziyarat",
            "munajat_lib": "munajat",
            "hadith_lib": "hadith",
            "wisdom_lib": "wisdom_featured",
        }

        content_type = content_map.get(prefix, "daily_dua")
        items = get_all_items(content_type)

        if items:
            kb = pagination_buttons(items, prefix, page=page, per_page=5)
        else:
            kb = back_button("menu:library")

        # Update message
        titles = {
            "dua_lib": "🤲 <b>الأدعية</b>",
            "ziyarat_lib": "🕌 <b>الزيارات</b>",
            "munajat_lib": "✨ <b>المناجيات</b>",
            "hadith_lib": "📖 <b>الأحاديث</b>",
            "wisdom_lib": "💎 <b>الحكم</b>",
        }

        await call.message.edit_text(
            titles.get(prefix, "📚 المكتبة"),
            reply_markup=kb,
            parse_mode="HTML"
        )
        await call.answer()
    elif action == "item":
        content_id = parts[2]
        content_map = {
            "dua_lib": ("daily_dua", format_dua),
            "ziyarat_lib": ("ziyarat", format_ziyarat),
            "munajat_lib": ("munajat", format_munajat),
            "hadith_lib": ("hadith", format_hadith),
            "wisdom_lib": ("wisdom_featured", format_wisdom),
        }

        info = content_map.get(prefix)
        if info:
            content_type, formatter = info
            # Try wisdom_short if featured not found
            item = get_content_by_id(content_type, content_id)
            if not item and content_type == "wisdom_featured":
                item = get_content_by_id("wisdom_short", content_id)

            if item:
                # ✅ الفحص الذكي: إذا كان المحتوى PDF نرسله كملف
                if item.get("is_pdf") and item.get("file_id"):
                    try:
                        await call.message.delete() # حذف رسالة القائمة
                    except Exception:
                        pass
                    await call.message.answer_document(
                        document=item["file_id"],
                        caption=f"📿 <b>{item.get('title', 'محتوى')}</b>\n\nنسألكم الدعاء 🤲",
                        parse_mode="HTML"
                    )
                    await call.answer("تم إرسال الملف بنجاح ✅")
                    return

                # إذا كان محتوى نصي عادي
                text = formatter(item)
                _back_target_map = {
                    "daily_dua":       "library:duas",
                    "ziyarat":         "library:ziyarat",
                    "munajat":         "library:munajat",
                    "hadith":          "library:hadith",
                    "wisdom_featured": "library:wisdom",
                    "wisdom_short":    "library:wisdom",
                }
                back_target = _back_target_map.get(content_type, "menu:library")
                fav_type = {"wisdom_featured": "wisdom", "wisdom_short": "wisdom"}.get(content_type, content_type)
                is_fav = db.is_favorite(call.from_user.id, fav_type, content_id)
                await call.message.edit_text(
                    text, parse_mode="HTML",
                    reply_markup=content_actions_keyboard(fav_type, content_id, back_target, is_fav)
                )
            else:
                await call.answer("لم يتم العثور على المحتوى.", show_alert=True)




# ═══════════════════════════════════════════════════════════
# FAVORITES HANDLERS
# ═══════════════════════════════════════════════════════════

async def callback_favorites_menu(call: CallbackQuery):
    """Show favorites main menu."""
    count = db.get_favorites_count(call.from_user.id)
    text = (
        f"⭐ <b>مفضلاتي</b>\n\n"
        f"لديك <b>{count}</b> عنصر محفوظ.\n"
        "اختر النوع لعرض المحفوظات:"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=favorites_menu())
    await call.answer()


async def callback_favorites_list(call: CallbackQuery):
    """Show paginated list of favorites for a specific content type."""
    parts = call.data.split(":")
    content_type = parts[2]
    page = int(parts[3]) if len(parts) > 3 else 0

    type_labels = {
        "hadith":    "📖 أحاديث محفوظة",
        "wisdom":    "💎 حكم محفوظة",
        "daily_dua": "🤲 أدعية محفوظة",
        "munajat":   "✨ مناجيات محفوظة",
        "ziyarat":   "🕌 زيارات محفوظة",
    }
    label = type_labels.get(content_type, "⭐ محفوظات")
    favs = db.get_favorites(call.from_user.id, content_type)

    if not favs:
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(make_button("🔙 المفضلة", "menu:favorites"))
        await call.message.edit_text(
            f"{label}\n\nلا يوجد محتوى محفوظ من هذا النوع.",
            parse_mode="HTML", reply_markup=kb
        )
        await call.answer()
        return

    per_page = 5
    total_pages = max(1, (len(favs) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    chunk = favs[start:start + per_page]

    kb = InlineKeyboardMarkup(row_width=1)
    for fav in chunk:
        title = fav.get("title") or fav["content_id"]
        btn_label = (title[:44] + "…") if len(title) > 45 else title
        kb.add(make_button(btn_label, f"fav:view:{content_type}:{fav['content_id']}"))

    nav_row = []
    if page > 0:
        nav_row.append(make_button("◀️ السابق", f"fav:list:{content_type}:{page - 1}"))
    if page < total_pages - 1:
        nav_row.append(make_button("التالي ▶️", f"fav:list:{content_type}:{page + 1}"))
    if nav_row:
        kb.row(*nav_row)
    kb.add(make_button("🔙 المفضلة", "menu:favorites"))

    await call.message.edit_text(
        f"{label}\n\n({len(favs)} عنصر، صفحة {page + 1}/{total_pages}):",
        parse_mode="HTML", reply_markup=kb
    )
    await call.answer()


async def callback_favorites_view(call: CallbackQuery):
    """View a specific favorite item with remove button."""
    parts = call.data.split(":")
    content_type = parts[2]
    content_id = parts[3]

    formatters = {
        "hadith":    format_hadith,
        "wisdom":    format_wisdom,
        "daily_dua": format_dua,
        "munajat":   format_munajat,
        "ziyarat":   format_ziyarat,
    }
    item = get_content_by_id(content_type, content_id)
    formatter = formatters.get(content_type)

    if not item or not formatter:
        await call.answer("لم يتم العثور على المحتوى.", show_alert=True)
        return

    text = formatter(item)
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        make_button("💔 إزالة من المفضلة", f"fav:rm:{content_type}:{content_id}"),
        make_button("🔙 المفضلة", f"fav:list:{content_type}:0"),
    )
    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await call.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()


async def callback_fav_toggle(call: CallbackQuery):
    """Add or remove an item from favorites, then refresh the button."""
    parts = call.data.split(":")
    action = parts[1]        # "add" or "rm"
    content_type = parts[2]
    content_id = parts[3]
    user_id = call.from_user.id

    if action == "add":
        item = get_content_by_id(content_type, content_id)
        title = ""
        if item:
            title = (item.get("title") or item.get("text", ""))[:60]
        db.add_favorite(user_id, content_type, content_id, title)
        new_action, new_label = "rm", "💔 إزالة من المفضلة"
        await call.answer("⭐ تم الحفظ في المفضلة!")
    else:
        db.remove_favorite(user_id, content_type, content_id)
        new_action, new_label = "add", "⭐ أضف للمفضلة"
        await call.answer("💔 تم الإزالة من المفضلة.")

    try:
        old_kb = call.message.reply_markup
        new_kb = InlineKeyboardMarkup(row_width=1)
        for row in old_kb.inline_keyboard:
            new_row = []
            for btn in row:
                cd = btn.callback_data or ""
                if cd.startswith("fav:add:") or cd.startswith("fav:rm:"):
                    new_row.append(InlineKeyboardButton(
                        text=new_label,
                        callback_data=f"fav:{new_action}:{content_type}:{content_id}"
                    ))
                else:
                    new_row.append(btn)
            new_kb.row(*new_row)
        await call.message.edit_reply_markup(reply_markup=new_kb)
    except Exception as e:
        logger.warning(f"Keyboard update error: {e}")


# ═══════════════════════════════════════════════════════════
# ADMIN HANDLERS
# ═══════════════════════════════════════════════════════════

def _is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


async def cmd_stats(message: Message):
    """Admin: display bot statistics."""
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


async def cmd_broadcast(message: Message):
    """Admin: broadcast a message to all users."""
    if not _is_admin(message.from_user.id):
        return

    text = message.get_args()
    if not text:
        await message.answer(
            "📢 <b>بث رسالة لجميع المستخدمين:</b>\n"
            "<code>/broadcast نص الرسالة</code>",
            parse_mode="HTML"
        )
        return

    users = db.get_all_users()
    await message.answer(f"📢 جاري الإرسال إلى {len(users)} مستخدم…")

    sent = failed = 0
    for user in users:
        try:
            await message.bot.send_message(user["user_id"], text, parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await message.answer(
        f"✅ <b>اكتمل البث</b>\n\n• تم الإرسال: {sent}\n• فشل: {failed}",
        parse_mode="HTML"
    )


async def cmd_content_status(message: Message):
    """Admin: display content files health report."""
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


async def cmd_errors(message: Message):
    """Admin: show recent error log entries."""
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


async def cmd_id(message: Message):
    """Send user's Telegram ID (useful for admin setup)."""
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
# REGISTER HANDLERS
# ═══════════════════════════════════════════════════════════

def register_handlers(dp: Dispatcher):
    """Register all handlers with the dispatcher."""

    # ─── Commands ───
    dp.register_message_handler(cmd_start, commands=["start"])
    dp.register_message_handler(cmd_menu, commands=["menu"])
    dp.register_message_handler(cmd_prayer, commands=["prayer"])
    dp.register_message_handler(cmd_event, commands=["event"])
    dp.register_message_handler(cmd_daily, commands=["daily"])
    dp.register_message_handler(cmd_subs, commands=["subs", "subscriptions"])
    dp.register_message_handler(cmd_about, commands=["about", "help"])
    dp.register_message_handler(cmd_city, commands=["city"])

    # ─── Main Menu Callbacks ───
    dp.register_callback_query_handler(callback_main_menu, lambda c: c.data == "menu:main")
    dp.register_callback_query_handler(callback_ibadat, lambda c: c.data == "menu:ibadat")
    dp.register_callback_query_handler(callback_library, lambda c: c.data == "menu:library")
    dp.register_callback_query_handler(callback_prayer, lambda c: c.data == "menu:prayer")
    dp.register_callback_query_handler(callback_events, lambda c: c.data == "menu:events")
    dp.register_callback_query_handler(callback_daily, lambda c: c.data == "menu:daily")
    dp.register_callback_query_handler(callback_settings, lambda c: c.data == "menu:settings")

    # ─── Ibadat Callbacks ───
    dp.register_callback_query_handler(callback_ibadat_day_works, lambda c: c.data == "ibadat:day_works")
    dp.register_callback_query_handler(callback_ibadat_night_works, lambda c: c.data == "ibadat:night_works")
    dp.register_callback_query_handler(callback_ibadat_dua_today, lambda c: c.data == "ibadat:dua_today")
    dp.register_callback_query_handler(callback_ibadat_taqibat, lambda c: c.data == "ibadat:taqibat")
    dp.register_callback_query_handler(callback_ibadat_what_to_read, lambda c: c.data == "ibadat:what_to_read")

    # ─── Taqibat Callbacks ───
    dp.register_callback_query_handler(callback_taqibat, lambda c: c.data.startswith("taqibat:"))

    # ─── Library Callbacks ───
    dp.register_callback_query_handler(callback_library_duas, lambda c: c.data == "library:duas")
    dp.register_callback_query_handler(callback_library_ziyarat, lambda c: c.data == "library:ziyarat")
    dp.register_callback_query_handler(callback_library_munajat, lambda c: c.data == "library:munajat")
    dp.register_callback_query_handler(callback_library_hadith, lambda c: c.data == "library:hadith")
    dp.register_callback_query_handler(callback_library_wisdom, lambda c: c.data == "library:wisdom")

    # ─── Random Content ───
    dp.register_callback_query_handler(callback_random_dua, lambda c: c.data == "dua:random")
    dp.register_callback_query_handler(callback_random_ziyarat, lambda c: c.data == "ziyarat:random")
    dp.register_callback_query_handler(callback_random_munajat, lambda c: c.data == "munajat:random")

    # ─── Prayer Callbacks ───
    dp.register_callback_query_handler(callback_prayer_times, lambda c: c.data == "prayer:times")
    dp.register_callback_query_handler(callback_prayer_next, lambda c: c.data == "prayer:next")
    dp.register_callback_query_handler(callback_prayer_taqibat, lambda c: c.data == "prayer:taqibat")
    dp.register_callback_query_handler(callback_prayer_reminder, lambda c: c.data == "prayer:reminder")

    # ─── Events Callbacks ───
    dp.register_callback_query_handler(callback_event_today, lambda c: c.data == "event:today")
    dp.register_callback_query_handler(callback_event_upcoming, lambda c: c.data == "event:upcoming")
    dp.register_callback_query_handler(callback_event_works, lambda c: c.data == "event:works")
    dp.register_callback_query_handler(callback_event_calendar, lambda c: c.data == "event:calendar")

    # ─── Daily Content Callbacks ───
    dp.register_callback_query_handler(callback_daily_hadith, lambda c: c.data == "daily:hadith")
    dp.register_callback_query_handler(callback_daily_wisdom, lambda c: c.data == "daily:wisdom")
    dp.register_callback_query_handler(callback_daily_dua, lambda c: c.data == "daily:dua")
    dp.register_callback_query_handler(callback_daily_munajat, lambda c: c.data == "daily:munajat")
    dp.register_callback_query_handler(callback_daily_random, lambda c: c.data == "daily:random")

    # ─── Settings Callbacks ───
    dp.register_callback_query_handler(callback_settings_subs, lambda c: c.data == "settings:subs")
    dp.register_callback_query_handler(callback_toggle_subscription, lambda c: c.data.startswith("sub_toggle:"))
    dp.register_callback_query_handler(callback_settings_city, lambda c: c.data == "settings:city")
    dp.register_callback_query_handler(callback_settings_timezone, lambda c: c.data == "settings:timezone")
    dp.register_callback_query_handler(callback_settings_about, lambda c: c.data == "settings:about")

    # ─── Pagination ───
    dp.register_callback_query_handler(callback_pagination, lambda c: c.data.startswith(("dua_lib:", "ziyarat_lib:", "munajat_lib:", "hadith_lib:", "wisdom_lib:")))

    # ─── Favorites ───
    dp.register_callback_query_handler(callback_favorites_menu, lambda c: c.data == "menu:favorites")
    dp.register_callback_query_handler(callback_favorites_list, lambda c: c.data.startswith("fav:list:"))
    dp.register_callback_query_handler(callback_favorites_view, lambda c: c.data.startswith("fav:view:"))
    dp.register_callback_query_handler(callback_fav_toggle, lambda c: c.data.startswith(("fav:add:", "fav:rm:")))

    # ─── Admin Commands ───
    dp.register_message_handler(cmd_stats, commands=["stats"])
    dp.register_message_handler(cmd_broadcast, commands=["broadcast"])
    dp.register_message_handler(cmd_content_status, commands=["content_status"])
    dp.register_message_handler(cmd_errors, commands=["errors"])

    # ─── User ID Helper ───
    dp.register_message_handler(cmd_id, commands=["id", "myid"])
