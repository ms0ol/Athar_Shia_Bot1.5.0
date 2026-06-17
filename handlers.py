"""
Athar Shia Bot - Handlers
بوت آثار الشيعة - معالجات الأوامر والأزرار
"""

import random
from aiogram import types, Dispatcher
from aiogram.types import CallbackQuery, Message

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
    subscriptions_settings_menu, back_button, pagination_buttons
)


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
        text += f"{dua.get('text', '')[:500]}...\n\n"

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
    """Handle today's dua."""
    dua = get_weekly_dua()
    if dua:
        text = format_weekly_dua(dua)
    else:
        # Fallback to random dua
        dua = get_random_item("daily_dua", call.from_user.id)
        if dua:
            text = format_dua(dua)
        else:
            text = "🤲 لا يوجد دعاء متوفر حالياً."

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:ibadat"))
    await call.answer()


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

    formatters = {
        "hadith": format_hadith,
        "wisdom_short": format_wisdom,
        "munajat": format_munajat,
        "daily_dua": format_dua,
    }

    text = formatters[choice](item)
    db.mark_content_sent(user_id, choice, item["id"])

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

    if data and data.get("items"):
        text = format_taqibat(data, prayer_names.get(prayer, prayer))
    else:
        text = f"📿 <b>تعقيبات صلاة {prayer_names.get(prayer, prayer)}</b>\n\n"
        text += "سيتم إضافة المحتوى قريباً إن شاء الله."

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:ibadat"))
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
    """Handle random dua."""
    item = get_random_item("daily_dua", call.from_user.id)
    if item:
        db.mark_content_sent(call.from_user.id, "daily_dua", item["id"])
        text = format_dua(item)
    else:
        text = "🤲 لا يوجد محتوى متوفر حالياً."

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:library"))
    await call.answer()


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
        item = get_random_item("wisdom_short", call.from_user.id)
    if not item:
        item = get_random_item("wisdom_deep", call.from_user.id)

    if item:
        db.mark_content_sent(call.from_user.id, "wisdom", item["id"])
        text = format_wisdom(item)
    else:
        text = "💎 لا يوجد محتوى متوفر حالياً."

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:daily"))
    await call.answer()


async def callback_daily_dua(call: CallbackQuery):
    """Handle daily dua."""
    item = get_random_item("daily_dua", call.from_user.id)
    if item:
        db.mark_content_sent(call.from_user.id, "daily_dua", item["id"])
        text = format_dua(item)
    else:
        text = "🤲 لا يوجد محتوى متوفر حالياً."

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:daily"))
    await call.answer()


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
    """Handle random daily content."""
    user_id = call.from_user.id
    content = get_daily_content(user_id)

    if not content:
        await call.answer("لا يوجد محتوى متوفر حالياً.", show_alert=True)
        return

    # Send each content type as a separate message
    first = True
    for key, item in content.items():
        formatters = {
            "hadith": format_hadith,
            "wisdom": format_wisdom,
            "dua": format_dua,
            "munajat": format_munajat,
        }
        text = formatters.get(key, lambda x: str(x))(item)

        if first:
            await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:daily"))
            first = False
        else:
            await call.message.answer(text, parse_mode="HTML")

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
        "بغداد": (33.3152, 44.3661),
        "كربلاء": (32.6160, 44.0248),
        "النجف": (31.9924, 44.3140),
        "بصرة": (30.5156, 47.7804),
        "سامراء": (34.2009, 43.8738),
        "كاظمية": (33.3791, 44.3368),
        "طهران": (35.6892, 51.3890),
        "قم": (34.6401, 50.8764),
        "مشهد": (36.2605, 59.6168),
        "كربلاء المقدسة": (32.6160, 44.0248),
        "النجف الأشرف": (31.9924, 44.3140),
    }

    coords = city_coords.get(city_name, (33.3152, 44.3661))
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
            kb = pagination_buttons(items, prefix.replace("_lib", ""), page=page, per_page=5)
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
                text = formatter(item)
                await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button(f"library:{content_type.split('_')[0] if '_' in content_type else content_type}s"))
            else:
                await call.answer("لم يتم العثور على المحتوى.", show_alert=True)


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
