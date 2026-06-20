"""
Athar Shia Bot - Navigation Service
بوت آثار الشيعة - خدمة التنقل والقوائم
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ─── Helper Functions ───

def make_button(text: str, callback: str) -> InlineKeyboardButton:
    """Create a single inline keyboard button."""
    return InlineKeyboardButton(text=text, callback_data=callback)


def make_row(*buttons) -> list:
    """Create a row of buttons."""
    return list(buttons)


# ─── Main Menu ───

def main_menu() -> InlineKeyboardMarkup:
    """Build the main menu keyboard."""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        make_button("📿 العبادات اليومية", "menu:ibadat"),
        make_button("📚 المكتبة الدينية", "menu:library"),
        make_button("🕌 الصلاة والأذان", "menu:prayer"),
        make_button("🗓 المناسبات والأعمال", "menu:events"),
        make_button("✨ المحتوى اليومي", "menu:daily"),
        make_button("⭐ مفضلاتي", "menu:favorites"),
        make_button("⚙️ إعداداتي", "menu:settings"),
    )
    return kb


# ─── Ibadat (Daily Worship) Menu ───

def ibadat_menu() -> InlineKeyboardMarkup:
    """Build the daily worship menu."""
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        make_button("📅 أعمال اليوم", "ibadat:day_works"),
        make_button("🌙 أعمال الليلة", "ibadat:night_works"),
        make_button("🤲 دعاء اليوم", "ibadat:dua_today"),
        make_button("📿 تعقيبات الصلاة", "ibadat:taqibat"),
        make_button("✨ ماذا أقرأ الآن؟", "ibadat:what_to_read"),
        make_button("🔙 الرئيسية", "menu:main"),
    )
    return kb


def taqibat_menu() -> InlineKeyboardMarkup:
    """Build taqibat submenu."""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        make_button("🌅 الفجر", "taqibat:fajr"),
        make_button("☀️ الظهر", "taqibat:dhuhr"),
        make_button("🌇 المغرب", "taqibat:maghrib"),
        make_button("🌙 العشاء", "taqibat:isha"),
        make_button("🔙 العبادات", "menu:ibadat"),
    )
    return kb


# ─── Library Menu ───

def library_menu() -> InlineKeyboardMarkup:
    """Build the library menu."""
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        make_button("🤲 الأدعية", "library:duas"),
        make_button("🕌 الزيارات", "library:ziyarat"),
        make_button("✨ المناجيات", "library:munajat"),
        make_button("📖 الأحاديث", "library:hadith"),
        make_button("💎 الحكم", "library:wisdom"),
        make_button("🔙 الرئيسية", "menu:main"),
    )
    return kb


def library_duas_menu() -> InlineKeyboardMarkup:
    """Build duas list menu (populated from JSON)."""
    kb = InlineKeyboardMarkup(row_width=1)
    # Will be populated dynamically in handler
    kb.add(
        make_button("🎲 دعاء عشوائي", "dua:random"),
        make_button("🔙 المكتبة", "menu:library"),
    )
    return kb


def library_ziyarat_menu() -> InlineKeyboardMarkup:
    """Build ziyarat list menu."""
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        make_button("🎲 زيارة عشوائية", "ziyarat:random"),
        make_button("🔙 المكتبة", "menu:library"),
    )
    return kb


def library_munajat_menu() -> InlineKeyboardMarkup:
    """Build munajat list menu."""
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        make_button("🎲 مناجاة عشوائية", "munajat:random"),
        make_button("🔙 المكتبة", "menu:library"),
    )
    return kb


# ─── Prayer Menu ───

def prayer_menu() -> InlineKeyboardMarkup:
    """Build the prayer menu."""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        make_button("🕐 مواقيت الصلاة", "prayer:times"),
        make_button("📍 الصلاة القادمة", "prayer:next"),
        make_button("📿 التعقيبات", "prayer:taqibat"),
        make_button("🔔 تذكير الصلاة", "prayer:reminder"),
        make_button("🔙 الرئيسية", "menu:main"),
    )
    return kb


# ─── Events Menu ───

def events_menu() -> InlineKeyboardMarkup:
    """Build the events menu."""
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        make_button("🗓 مناسبة اليوم", "event:today"),
        make_button("📅 المناسبات القادمة", "event:upcoming"),
        make_button("✨ أعمال المناسبة", "event:works"),
        make_button("📖 التقويم الهجري", "event:calendar"),
        make_button("🔙 الرئيسية", "menu:main"),
    )
    return kb


# ─── Daily Content Menu ───

def daily_menu() -> InlineKeyboardMarkup:
    """Build the daily content menu."""
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        make_button("📖 حديث اليوم", "daily:hadith"),
        make_button("💎 حكمة اليوم", "daily:wisdom"),
        make_button("🤲 دعاء اليوم", "daily:dua"),
        make_button("✨ مناجاة اليوم", "daily:munajat"),
        make_button("🎲 محتوى عشوائي", "daily:random"),
        make_button("🔙 الرئيسية", "menu:main"),
    )
    return kb


# ─── Settings Menu ───

def settings_menu() -> InlineKeyboardMarkup:
    """Build the settings menu."""
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        make_button("🔔 اشتراكاتي", "settings:subs"),
        make_button("🕌 المدينة", "settings:city"),
        make_button("🕐 المنطقة الزمنية", "settings:timezone"),
        make_button("ℹ️ حول البوت", "settings:about"),
        make_button("🔙 الرئيسية", "menu:main"),
    )
    return kb


def subscriptions_settings_menu(user_subs: dict) -> InlineKeyboardMarkup:
    """Build subscriptions settings menu."""
    kb = InlineKeyboardMarkup(row_width=1)

    sub_buttons = [
        ("📖 حديث يومي", "sub_toggle:hadith_daily"),
        ("💎 حكمة يومية", "sub_toggle:wisdom_daily"),
        ("🤲 دعاء يومي", "sub_toggle:dua_daily"),
        ("✨ مناجاة يومية", "sub_toggle:munajat_daily"),
        ("🕌 تذكير الصلاة", "sub_toggle:prayer_reminder"),
        ("📅 تذكير المناسبات", "sub_toggle:event_reminder"),
    ]

    for name, callback in sub_buttons:
        # Extract key from callback
        key = callback.split(":")[1]
        status = "✅" if user_subs.get(key, False) else "❌"
        kb.add(make_button(f"{status} {name}", callback))

    kb.add(make_button("🔙 الإعدادات", "menu:settings"))
    return kb


# ─── Back Buttons ───

def back_button(target: str) -> InlineKeyboardMarkup:
    """Create a simple back button."""
    kb = InlineKeyboardMarkup()
    kb.add(make_button("🔙 رجوع", target))
    return kb


def pagination_buttons(items: list, prefix: str, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    """Create pagination buttons for a list of items."""
    kb = InlineKeyboardMarkup(row_width=1)

    total_pages = (len(items) + per_page - 1) // per_page
    start = page * per_page
    end = min(start + per_page, len(items))

    for item in items[start:end]:
        title = item.get("title") or item.get("author") or ""
        text_preview = item.get("text", "")
        if title:
            label = f"{title[:45]}…" if len(title) > 45 else title
        elif text_preview:
            label = f"{text_preview[:45]}…" if len(text_preview) > 45 else text_preview
        else:
            label = item.get("id", "—")
        kb.add(make_button(label, f"{prefix}:item:{item.get('id', '')}"))

    # Pagination controls
    nav_row = []
    if page > 0:
        nav_row.append(make_button("◀️ السابق", f"{prefix}:page:{page - 1}"))
    if page < total_pages - 1:
        nav_row.append(make_button("التالي ▶️", f"{prefix}:page:{page + 1}"))

    if nav_row:
        kb.row(*nav_row)

    return kb


# ─── Share Button ───

def share_button(content_type: str, content_id: str) -> InlineKeyboardMarkup:
    """Create a share button for content."""
    kb = InlineKeyboardMarkup()
    kb.add(make_button("📤 مشاركة", f"share:{content_type}:{content_id}"))
    return kb


# ─── Favorites Menu ───

def favorites_menu() -> InlineKeyboardMarkup:
    """Build favorites main menu."""
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        make_button("📖 أحاديث محفوظة", "fav:list:hadith:0"),
        make_button("💎 حكم محفوظة", "fav:list:wisdom:0"),
        make_button("🤲 أدعية محفوظة", "fav:list:daily_dua:0"),
        make_button("✨ مناجيات محفوظة", "fav:list:munajat:0"),
        make_button("🕌 زيارات محفوظة", "fav:list:ziyarat:0"),
        make_button("🔙 الرئيسية", "menu:main"),
    )
    return kb


def content_actions_keyboard(content_type: str, content_id: str,
                              back_target: str, is_fav: bool = False) -> InlineKeyboardMarkup:
    """Build action keyboard under content: favorites toggle + back button."""
    kb = InlineKeyboardMarkup(row_width=1)
    if is_fav:
        fav_btn = make_button("💔 إزالة من المفضلة", f"fav:rm:{content_type}:{content_id}")
    else:
        fav_btn = make_button("⭐ أضف للمفضلة", f"fav:add:{content_type}:{content_id}")
    kb.add(fav_btn, make_button("🔙 رجوع", back_target))
    return kb
