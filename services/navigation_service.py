"""
Athar Shia Bot - Navigation Service
بوت اثر الشيعة - خدمة التنقل والقوائم
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def make_button(text: str, callback: str) -> InlineKeyboardButton:
    """Create a single inline keyboard button."""
    return InlineKeyboardButton(text=text, callback_data=callback)


def _kb(*rows) -> InlineKeyboardMarkup:
    """Build an InlineKeyboardMarkup from rows of buttons."""
    return InlineKeyboardMarkup(inline_keyboard=list(rows))


def _row(*buttons) -> list:
    return list(buttons)


def main_menu() -> InlineKeyboardMarkup:
    return _kb(
        _row(make_button("📿 العبادات اليومية", "menu:ibadat"), make_button("📚 المكتبة الدينية", "menu:library")),
        _row(make_button("🕌 الصلاة والأذان", "menu:prayer"), make_button("🗓 المناسبات والأعمال", "menu:events")),
        _row(make_button("✨ المحتوى اليومي", "menu:daily"), make_button("⭐ مفضلاتي", "menu:favorites")),
        _row(make_button("⚙️ إعداداتي", "menu:settings")),
    )


def ibadat_menu() -> InlineKeyboardMarkup:
    return _kb(
        _row(make_button("📅 أعمال اليوم", "ibadat:day_works")),
        _row(make_button("🌙 أعمال الليلة", "ibadat:night_works")),
        _row(make_button("🤲 دعاء اليوم", "ibadat:dua_today")),
        _row(make_button("🕌 زيارة اليوم", "ibadat:ziyarat_today")),
        _row(make_button("✨ ماذا أقرأ الآن؟", "ibadat:what_to_read")),
        _row(make_button("🏠 الرئيسية", "menu:main")),
    )


def taqibat_menu() -> InlineKeyboardMarkup:
    return _kb(
        _row(make_button("🌅 الفجر", "taqibat:fajr"), make_button("☀️ الظهر", "taqibat:dhuhr")),
        _row(make_button("🌇 المغرب", "taqibat:maghrib"), make_button("🌙 العشاء", "taqibat:isha")),
        _row(make_button("🔙 العبادات", "menu:ibadat")),
    )


def library_menu() -> InlineKeyboardMarkup:
    return _kb(
        _row(make_button("🤲 الأدعية", "library:duas")),
        _row(make_button("🕌 الزيارات", "library:ziyarat")),
        _row(make_button("✨ المناجيات", "library:munajat")),
        _row(make_button("📖 الأحاديث", "library:hadith")),
        _row(make_button("💎 الحكم", "library:wisdom")),
        _row(make_button("🏠 الرئيسية", "menu:main")),
    )


def library_duas_menu() -> InlineKeyboardMarkup:
    return _kb(
        _row(make_button("🎲 دعاء عشوائي", "dua:random")),
        _row(make_button("🔙 المكتبة", "menu:library")),
    )


def library_ziyarat_menu() -> InlineKeyboardMarkup:
    return _kb(
        _row(make_button("🎲 زيارة عشوائية", "ziyarat:random")),
        _row(make_button("🔙 المكتبة", "menu:library")),
    )


def library_munajat_menu() -> InlineKeyboardMarkup:
    return _kb(
        _row(make_button("🎲 مناجاة عشوائية", "munajat:random")),
        _row(make_button("🔙 المكتبة", "menu:library")),
    )


def prayer_menu() -> InlineKeyboardMarkup:
    return _kb(
        _row(make_button("🕐 مواقيت الصلاة", "prayer:times"), make_button("📍 الصلاة القادمة", "prayer:next")),
        _row(make_button("📿 التعقيبات", "prayer:taqibat"), make_button("🔔 تذكير الصلاة", "prayer:reminder")),
        _row(make_button("🏠 الرئيسية", "menu:main")),
    )


def events_menu() -> InlineKeyboardMarkup:
    return _kb(
        _row(make_button("🗓 مناسبة اليوم", "event:today")),
        _row(make_button("📅 المناسبات القادمة", "event:upcoming")),
        _row(make_button("✨ أعمال المناسبة", "event:works")),
        _row(make_button("📖 التقويم الهجري", "event:calendar")),
        _row(make_button("🏠 الرئيسية", "menu:main")),
    )


def daily_menu() -> InlineKeyboardMarkup:
    return _kb(
        _row(make_button("📖 حديث اليوم", "daily:hadith")),
        _row(make_button("💎 حكمة اليوم", "daily:wisdom")),
        _row(make_button("🤲 دعاء اليوم", "daily:dua")),
        _row(make_button("✨ مناجاة اليوم", "daily:munajat")),
        _row(make_button("🎲 محتوى عشوائي", "daily:random")),
        _row(make_button("🏠 الرئيسية", "menu:main")),
    )


def settings_menu() -> InlineKeyboardMarkup:
    return _kb(
        _row(make_button("🔔 اشتراكاتي", "settings:subs")),
        _row(make_button("📍 الموقع الجغرافي", "settings:city")),
        _row(make_button("🕐 المنطقة الزمنية", "settings:timezone")),
        _row(make_button("ℹ️ حول البوت", "settings:about")),
        _row(make_button("🏠 الرئيسية", "menu:main")),
    )


def location_settings_menu() -> InlineKeyboardMarkup:
    return _kb(
        _row(make_button("📡 مشاركة موقعي الحالي (GPS) ← موصى به", "location:request_gps")),
        _row(make_button("🗺 اختيار المحافظة يدوياً", "location:manual")),
        _row(make_button("🔙 الإعدادات", "menu:settings")),
    )


def governorates_keyboard() -> InlineKeyboardMarkup:
    from services.location_data import IRAQ_CITIES
    rows = []
    govs = list(IRAQ_CITIES.keys())
    for i in range(0, len(govs), 2):
        row = [make_button(govs[i], f"location:gov:{govs[i]}")]
        if i + 1 < len(govs):
            row.append(make_button(govs[i + 1], f"location:gov:{govs[i+1]}"))
        rows.append(row)
    rows.append(_row(make_button("🔙 رجوع", "settings:city")))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def districts_keyboard(governorate: str) -> InlineKeyboardMarkup:
    from services.location_data import IRAQ_CITIES
    districts = IRAQ_CITIES.get(governorate, {})
    rows = []
    for district in districts.keys():
        safe_district = district.replace(":", "_")
        rows.append(_row(make_button(district, f"location:district:{governorate}:{safe_district}")))
    rows.append(_row(make_button("🔙 المحافظات", "location:manual")))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def subscriptions_settings_menu(user_subs: dict) -> InlineKeyboardMarkup:
    sub_buttons = [
        ("📖 حديث يومي", "sub_toggle:hadith_daily"),
        ("💎 حكمة يومية", "sub_toggle:wisdom_daily"),
        ("🤲 دعاء يومي", "sub_toggle:dua_daily"),
        ("✨ مناجاة يومية", "sub_toggle:munajat_daily"),
        ("🕌 تذكير الصلاة", "sub_toggle:prayer_reminder"),
        ("📅 تذكير المناسبات", "sub_toggle:event_reminder"),
    ]
    rows = []
    for name, callback in sub_buttons:
        key = callback.split(":")[1]
        status = "✅" if user_subs.get(key, False) else "❌"
        rows.append(_row(make_button(f"{status} {name}", callback)))
    rows.append(_row(make_button("🔙 الإعدادات", "menu:settings")))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def taqibat_pagination_keyboard(prayer_type: str, page: int, total_pages: int) -> InlineKeyboardMarkup:
    rows = []
    nav_row = []
    if page > 0:
        nav_row.append(make_button("◀️ السابقة", f"taqibat_page:{prayer_type}:{page - 1}"))
    if page < total_pages - 1:
        nav_row.append(make_button("التالية ▶️", f"taqibat_page:{prayer_type}:{page + 1}"))
    if nav_row:
        rows.append(nav_row)
    rows.append(_row(make_button("🔙 رجوع", "ibadat:taqibat"), make_button("🏠 الرئيسية", "menu:main")))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_button(target: str) -> InlineKeyboardMarkup:
    return _kb(_row(make_button("🔙 رجوع", target)))


def pagination_buttons(items: list, prefix: str, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    total_pages = (len(items) + per_page - 1) // per_page
    start = page * per_page
    end = min(start + per_page, len(items))

    text_first_prefixes = ("hadith_lib", "wisdom_lib")
    title_first_prefixes = ("munajat_lib", "ziyarat_lib")

    rows = []
    for item in items[start:end]:
        text_preview = item.get("text", "")
        title = item.get("title") or item.get("author") or ""

        if prefix in text_first_prefixes:
            if text_preview:
                label = f"{text_preview[:45]}…" if len(text_preview) > 45 else text_preview
            elif title:
                label = f"{title[:45]}…" if len(title) > 45 else title
            else:
                label = item.get("id", "—")
        elif prefix in title_first_prefixes:
            if title:
                label = f"{title[:45]}…" if len(title) > 45 else title
            elif text_preview:
                label = f"{text_preview[:45]}…" if len(text_preview) > 45 else text_preview
            else:
                label = item.get("id", "—")
        else:
            if title:
                label = f"{title[:45]}…" if len(title) > 45 else title
            elif text_preview:
                label = f"{text_preview[:45]}…" if len(text_preview) > 45 else text_preview
            else:
                label = item.get("id", "—")
        rows.append(_row(make_button(label, f"{prefix}:item:{item.get('id', '')}")))

    nav_row = []
    if page > 0:
        nav_row.append(make_button("◀️ السابق", f"{prefix}:page:{page - 1}"))
    if page < total_pages - 1:
        nav_row.append(make_button("التالي ▶️", f"{prefix}:page:{page + 1}"))
    if nav_row:
        rows.append(nav_row)

    rows.append(_row(make_button("🏠 الرئيسية", "menu:main")))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def share_button(content_type: str, content_id: str) -> InlineKeyboardMarkup:
    return _kb(_row(make_button("📤 مشاركة", f"share:{content_type}:{content_id}")))


def admin_settings_menu() -> InlineKeyboardMarkup:
    return _kb(
        _row(make_button("🔔 تشغيل/إيقاف تنبيه الأعضاء الجدد", "admin:toggle_new_user")),
        _row(make_button("🏠 الرئيسية", "menu:main")),
    )


def favorites_menu() -> InlineKeyboardMarkup:
    return _kb(
        _row(make_button("📖 أحاديث محفوظة", "fav:list:hadith:0")),
        _row(make_button("💎 حكم محفوظة", "fav:list:wisdom:0")),
        _row(make_button("🤲 أدعية محفوظة", "fav:list:daily_dua:0")),
        _row(make_button("✨ مناجيات محفوظة", "fav:list:munajat:0")),
        _row(make_button("🕌 زيارات محفوظة", "fav:list:ziyarat:0")),
        _row(make_button("🏠 الرئيسية", "menu:main")),
    )


def content_actions_keyboard(content_type: str, content_id: str,
                              back_target: str, is_fav: bool = False) -> InlineKeyboardMarkup:
    if is_fav:
        fav_btn = make_button("💔 إزالة من المفضلة", f"fav:rm:{content_type}:{content_id}")
    else:
        fav_btn = make_button("⭐ أضف للمفضلة", f"fav:add:{content_type}:{content_id}")
    return _kb(
        _row(fav_btn),
        _row(make_button("🔙 رجوع", back_target)),
    )
