"""
handlers/daily.py — المحتوى اليومي، الاشتراكات، التصفح (pagination)، المفضلة
"""

import logging
import random

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

import database as db
from services.content_service import (
    get_random_item, get_all_items, get_content_by_id,
    format_hadith, format_wisdom, format_dua, format_munajat, format_ziyarat,
)
from services.subscription_service import (
    get_subscription_list, toggle_subscription, format_subscriptions_list,
)
from services.navigation_service import (
    daily_menu, subscriptions_settings_menu, back_button,
    pagination_buttons, favorites_menu, content_actions_keyboard, make_button,
)

logger = logging.getLogger(__name__)
router = Router(name="daily_router")


# ═══════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════

@router.message(Command("daily"))
async def cmd_daily(message: Message):
    await message.answer(
        "✨ <b>اختر المحتوى اليومي:</b>",
        reply_markup=daily_menu(),
        parse_mode="HTML"
    )


@router.message(Command("subs", "subscriptions"))
async def cmd_subs(message: Message):
    await _show_subscriptions(message)


# ═══════════════════════════════════════════════════════════
# SUBSCRIPTIONS HELPERS + CALLBACKS
# ═══════════════════════════════════════════════════════════

async def _show_subscriptions(message_or_call):
    user_id = message_or_call.from_user.id
    subs = get_subscription_list(user_id)
    text = format_subscriptions_list(subs)
    kb = subscriptions_settings_menu({s["key"]: s["is_active"] for s in subs})

    if isinstance(message_or_call, CallbackQuery):
        await message_or_call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await message_or_call.answer()
    else:
        await message_or_call.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "settings:subs")
async def callback_settings_subs(call: CallbackQuery):
    await _show_subscriptions(call)


@router.callback_query(F.data.startswith("sub_toggle:"))
async def callback_toggle_subscription(call: CallbackQuery):
    sub_key = call.data.split(":")[1]
    new_state = toggle_subscription(call.from_user.id, sub_key)

    subs = get_subscription_list(call.from_user.id)
    text = format_subscriptions_list(subs)
    await call.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=subscriptions_settings_menu({s["key"]: s["is_active"] for s in subs})
    )
    await call.answer("✅ تم" if new_state else "❌ تم الإلغاء")


# ═══════════════════════════════════════════════════════════
# DAILY CONTENT CALLBACKS
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "daily:hadith")
async def callback_daily_hadith(call: CallbackQuery):
    item = get_random_item("hadith", call.from_user.id)
    if item:
        db.mark_content_sent(call.from_user.id, "hadith", item["id"])
        text = format_hadith(item)
    else:
        text = "📖 لا يوجد محتوى متوفر حالياً."
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:daily"))
    await call.answer()


@router.callback_query(F.data == "daily:wisdom")
async def callback_daily_wisdom(call: CallbackQuery):
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


@router.callback_query(F.data == "daily:dua")
async def callback_daily_dua(call: CallbackQuery):
    from handlers.ibadat import _send_dua_pdf
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


@router.callback_query(F.data == "daily:munajat")
async def callback_daily_munajat(call: CallbackQuery):
    item = get_random_item("munajat", call.from_user.id)
    if item:
        db.mark_content_sent(call.from_user.id, "munajat", item["id"])
        text = format_munajat(item)
    else:
        text = "✨ لا يوجد محتوى متوفر حالياً."
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:daily"))
    await call.answer()


@router.callback_query(F.data == "daily:random")
async def callback_daily_random(call: CallbackQuery):
    from handlers.ibadat import _send_dua_pdf
    user_id = call.from_user.id

    options = [
        ("hadith",    format_hadith),
        ("wisdom",    format_wisdom),
        ("daily_dua", format_dua),
        ("munajat",   format_munajat),
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
# PAGINATION CALLBACKS
# ═══════════════════════════════════════════════════════════

_content_map_prefix = {
    "dua_lib":     "daily_dua",
    "ziyarat_lib": "ziyarat",
    "munajat_lib": "munajat",
    "hadith_lib":  "hadith",
    "wisdom_lib":  "wisdom_featured",
}

_titles_map = {
    "dua_lib":     "🤲 <b>الأدعية</b>",
    "ziyarat_lib": "🕌 <b>الزيارات</b>",
    "munajat_lib": "✨ <b>المناجيات</b>",
    "hadith_lib":  "📖 <b>الأحاديث</b>",
    "wisdom_lib":  "💎 <b>الحكم</b>",
}

_formatter_map = {
    "dua_lib":     ("daily_dua",       format_dua),
    "ziyarat_lib": ("ziyarat",         format_ziyarat),
    "munajat_lib": ("munajat",         format_munajat),
    "hadith_lib":  ("hadith",          format_hadith),
    "wisdom_lib":  ("wisdom_featured", format_wisdom),
}

_back_target_map = {
    "daily_dua":       "library:duas",
    "ziyarat":         "library:ziyarat",
    "munajat":         "library:munajat",
    "hadith":          "library:hadith",
    "wisdom_featured": "library:wisdom",
    "wisdom_short":    "library:wisdom",
}


@router.callback_query(
    F.data.startswith(("dua_lib:", "ziyarat_lib:", "munajat_lib:", "hadith_lib:", "wisdom_lib:"))
)
async def callback_pagination(call: CallbackQuery):
    parts = call.data.split(":")
    prefix = parts[0]
    action = parts[1]

    if action == "page":
        page = int(parts[2])
        content_type = _content_map_prefix.get(prefix, "daily_dua")
        items = get_all_items(content_type)
        kb = pagination_buttons(items, prefix, page=page, per_page=5) if items else back_button("menu:library")

        await call.message.edit_text(
            _titles_map.get(prefix, "📚 المكتبة"),
            reply_markup=kb,
            parse_mode="HTML"
        )
        await call.answer()

    elif action == "item":
        content_id = parts[2]
        info = _formatter_map.get(prefix)
        if not info:
            await call.answer("⚠️ خطأ في البيانات", show_alert=True)
            return

        content_type, formatter = info
        item = get_content_by_id(content_type, content_id)
        if not item and content_type == "wisdom_featured":
            item = get_content_by_id("wisdom_short", content_id)

        if not item:
            await call.answer("لم يتم العثور على المحتوى.", show_alert=True)
            return

        if item.get("is_pdf") and item.get("file_id"):
            try:
                await call.message.delete()
            except Exception:
                pass
            await call.message.answer_document(
                document=item["file_id"],
                caption=f"📿 <b>{item.get('title', 'محتوى')}</b>\n\nنسألكم الدعاء 🤲",
                parse_mode="HTML"
            )
            await call.answer("تم إرسال الملف بنجاح ✅")
            return

        text = formatter(item)
        back_target = _back_target_map.get(content_type, "menu:library")
        fav_type = {"wisdom_featured": "wisdom", "wisdom_short": "wisdom"}.get(content_type, content_type)
        is_fav = db.is_favorite(call.from_user.id, fav_type, content_id)
        await call.message.edit_text(
            text, parse_mode="HTML",
            reply_markup=content_actions_keyboard(fav_type, content_id, back_target, is_fav)
        )
        await call.answer()


# ═══════════════════════════════════════════════════════════
# FAVORITES CALLBACKS
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("fav:list:"))
async def callback_favorites_list(call: CallbackQuery):
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
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 المفضلة", callback_data="menu:favorites")]
        ])
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

    item_buttons = [
        [make_button(
            (fav.get("title") or fav["content_id"])[:44] + ("…" if len(fav.get("title") or fav["content_id"]) > 44 else ""),
            f"fav:view:{content_type}:{fav['content_id']}"
        )]
        for fav in chunk
    ]

    nav_row = []
    if page > 0:
        nav_row.append(make_button("◀️ السابق", f"fav:list:{content_type}:{page - 1}"))
    if page < total_pages - 1:
        nav_row.append(make_button("التالي ▶️", f"fav:list:{content_type}:{page + 1}"))

    rows = item_buttons
    if nav_row:
        rows = rows + [nav_row]
    rows = rows + [[make_button("🔙 المفضلة", "menu:favorites")]]

    kb = InlineKeyboardMarkup(inline_keyboard=rows)

    await call.message.edit_text(
        f"{label}\n\n({len(favs)} عنصر، صفحة {page + 1}/{total_pages}):",
        parse_mode="HTML", reply_markup=kb
    )
    await call.answer()


@router.callback_query(F.data.startswith("fav:view:"))
async def callback_favorites_view(call: CallbackQuery):
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
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [make_button("💔 إزالة من المفضلة", f"fav:rm:{content_type}:{content_id}")],
        [make_button("🔙 المفضلة", f"fav:list:{content_type}:0")],
    ])
    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await call.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith(("fav:add:", "fav:rm:")))
async def callback_fav_toggle(call: CallbackQuery):
    parts = call.data.split(":")
    action = parts[1]
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
        new_rows = []
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
            new_rows.append(new_row)
        await call.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=new_rows))
    except Exception as e:
        logger.warning(f"Keyboard update error: {e}")
