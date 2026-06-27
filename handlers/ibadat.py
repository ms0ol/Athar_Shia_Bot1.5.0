"""
handlers/ibadat.py — العبادات اليومية، التعقيبات، المكتبة، المحتوى العشوائي
"""

import logging
import random

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery

import database as db
from services.content_service import (
    get_random_item, get_all_items,
    format_hadith, format_wisdom, format_dua, format_munajat, format_ziyarat,
)
from services.event_service import (
    get_today_event, get_weekly_dua, get_weekly_ziyarat,
    get_today_hijri, format_hijri_date, format_weekly_dua,
)
from services.prayer_service import get_prayer_taqibat, format_taqibat_page
from services.navigation_service import (
    ibadat_menu, taqibat_menu,
    library_duas_menu, library_ziyarat_menu, library_munajat_menu,
    back_button, pagination_buttons, taqibat_pagination_keyboard,
)

logger = logging.getLogger(__name__)
router = Router(name="ibadat_router")

# ─── Tracker for PDFs sent in day_works ───
_day_works_pdf_msg: dict = {}

prayer_names = {
    "fajr": "الفجر", "dhuhr": "الظهر",
    "maghrib": "المغرب", "isha": "العشاء"
}


# ═══════════════════════════════════════════════════════════
# PDF HELPERS
# ═══════════════════════════════════════════════════════════

async def _send_dua_pdf(call: CallbackQuery, item: dict) -> bool:
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
    except TelegramBadRequest as e:
        logger.error(f"[DUA PDF] فشل إرسال {dua_id} ({title}): {e}")
        await call.answer(
            f"⚠️ ملف '{title}' غير متاح حالياً.\n"
            "يرجى إخبار المشرف لتحديث الملف عبر أمر /duas_status",
            show_alert=True
        )
        return False


async def _send_ziyarat_pdf(call: CallbackQuery, item: dict) -> bool:
    ziyarat_id = item.get("id", "")
    title = item.get("title", "زيارة")
    caption = f"🕌 <b>{title}</b>\n\nنسألكم الدعاء 🤲"

    file_id = item.get("file_id")
    if not file_id:
        await call.answer(f"⚠️ ملف '{title}' غير متاح حالياً.", show_alert=True)
        return False

    try:
        msg = await call.message.answer_document(
            document=file_id,
            caption=caption,
            parse_mode="HTML"
        )
        await call.answer("تم إرسال ملف الزيارة ✅")
        return msg
    except TelegramBadRequest as e:
        logger.error(f"[ZIYARAT PDF] فشل إرسال {ziyarat_id} ({title}): {e}")
        await call.answer(f"⚠️ ملف '{title}' غير متاح حالياً.", show_alert=True)
        return False


async def _cleanup_day_works_pdfs(user_id: int, bot) -> None:
    msg_ids = _day_works_pdf_msg.pop(user_id, [])
    for mid in msg_ids:
        try:
            await bot.delete_message(chat_id=user_id, message_id=mid)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
# IBADAT CALLBACKS
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "ibadat:day_works")
async def callback_ibadat_day_works(call: CallbackQuery):
    user_id = call.from_user.id
    hijri = get_today_hijri()
    dua = get_weekly_dua()
    ziyarat = get_weekly_ziyarat()

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
            text += "سيتم إرسال ملف الدعاء أدناه 👇\n\n"

    if ziyarat:
        text += f"🕌 <b>زيارة اليوم:</b> {ziyarat.get('title', '')}\n"
        ziyarat_text = ziyarat.get('text', '')
        if ziyarat_text:
            text += f"{ziyarat_text}\n\n"
        else:
            text += "سيتم إرسال ملف الزيارة أدناه 👇\n\n"

    text += "📿 تذكر: الصلاة على محمد وآل محمد في كل أحوالك 🌹"

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:ibadat"))

    tracked_ids = []

    if dua and dua.get("is_pdf") and dua.get("file_id"):
        dua_file_id = db.get_dua_file_id(dua.get("id", "")) or dua.get("file_id")
        try:
            dua_msg = await call.message.answer_document(
                document=dua_file_id,
                caption=f"📿 <b>{dua.get('title', 'دعاء اليوم')}</b>\n\nنسألكم الدعاء 🤲",
                parse_mode="HTML"
            )
            tracked_ids.append(dua_msg.message_id)
        except Exception as e:
            logger.error(f"[DAY_WORKS DUA PDF] {e}")

    if ziyarat and ziyarat.get("is_pdf") and ziyarat.get("file_id"):
        try:
            ziyarat_msg = await call.message.answer_document(
                document=ziyarat.get("file_id"),
                caption=f"🕌 <b>{ziyarat.get('title', 'زيارة اليوم')}</b>\n\nنسألكم الدعاء 🤲",
                parse_mode="HTML"
            )
            tracked_ids.append(ziyarat_msg.message_id)
        except Exception as e:
            logger.error(f"[DAY_WORKS ZIYARAT PDF] {e}")

    if tracked_ids:
        _day_works_pdf_msg[user_id] = tracked_ids

    await call.answer()


@router.callback_query(F.data == "ibadat:night_works")
async def callback_ibadat_night_works(call: CallbackQuery):
    hijri = get_today_hijri()

    text = f"🌙 <b>أعمال الليلة</b>\n"
    text += f"📆 {format_hijri_date(hijri)}\n\n"
    text += (
        "🌟 <b>من المستحبات:</b>\n\n"
        "• صلاة الليل (التهجد)\n"
        "• قراءة سورة الملك\n"
        "• قراءة سورة السجدة\n"
        "• الدعاء قبل النوم\n"
        "• الاستغفار 100 مرة\n"
        "• الصلاة على محمد وآل محمد 100 مرة\n"
        "• الدعاء بالمأثورات\n\n"
        "🤲 <i>اللهم بحق محمد وعلي وفاطمة والحسن والحسين\n"
        "علي ومحمد وجعفر وموسى وعلي ومحمد وعلي والحسن\n"
        "والمهدي اجعلنا من المقبولين</i>"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:ibadat"))
    await call.answer()


@router.callback_query(F.data == "ibadat:dua_today")
async def callback_ibadat_dua_today(call: CallbackQuery):
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


@router.callback_query(F.data == "ibadat:ziyarat_today")
async def callback_ibadat_ziyarat_today(call: CallbackQuery):
    ziyarat = get_weekly_ziyarat()

    if not ziyarat:
        await call.answer("🕌 لا توجد زيارة مخصصة لهذا اليوم حالياً.", show_alert=True)
        return

    if ziyarat.get("is_pdf") and ziyarat.get("file_id"):
        user_id = call.from_user.id
        try:
            ziyarat_msg = await call.message.answer_document(
                document=ziyarat["file_id"],
                caption=f"🕌 <b>{ziyarat.get('title', 'زيارة اليوم')}</b>\n\nنسألكم الدعاء 🤲",
                parse_mode="HTML"
            )
            existing = _day_works_pdf_msg.get(user_id, [])
            existing.append(ziyarat_msg.message_id)
            _day_works_pdf_msg[user_id] = existing
            await call.answer("تم إرسال ملف الزيارة ✅")
        except TelegramBadRequest as e:
            logger.error(f"[ZIYARAT TODAY] {e}")
            await call.answer("⚠️ ملف الزيارة غير متاح حالياً.", show_alert=True)
    elif ziyarat.get("text"):
        text = f"🕌 <b>{ziyarat.get('title', 'زيارة اليوم')}</b>\n\n{ziyarat['text']}"
        await call.message.edit_text(text[:4000], parse_mode="HTML", reply_markup=back_button("menu:ibadat"))
        await call.answer()
    else:
        await call.answer("⚠️ لا يوجد محتوى للزيارة.", show_alert=True)


@router.callback_query(F.data == "ibadat:taqibat")
async def callback_ibadat_taqibat(call: CallbackQuery):
    await call.message.edit_text(
        "📿 <b>تعقيبات الصلاة</b>\n\nاختر الصلاة:",
        reply_markup=taqibat_menu(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "ibadat:what_to_read")
async def callback_ibadat_what_to_read(call: CallbackQuery):
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
# TAQIBAT CALLBACKS
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("taqibat:"))
async def callback_taqibat(call: CallbackQuery):
    prayer = call.data.split(":")[1]
    data = get_prayer_taqibat(prayer)

    if data and "items" in data:
        items = data["items"]
        per_page = 5
        total_pages = max(1, (len(items) + per_page - 1) // per_page)
        chunk = items[0:per_page]

        text = format_taqibat_page(chunk, prayer_names.get(prayer, prayer), 0, total_pages)
        kb = taqibat_pagination_keyboard(prayer, 0, total_pages)
    else:
        text = f"📿 <b>تعقيبات صلاة {prayer_names.get(prayer, prayer)}</b>\n\nسيتم إضافة المحتوى قريباً إن شاء الله."
        kb = back_button("menu:ibadat")

    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await call.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("taqibat_page:"))
async def callback_taqibat_page(call: CallbackQuery):
    parts = call.data.split(":")
    prayer = parts[1]
    page = int(parts[2])

    data = get_prayer_taqibat(prayer)
    if not data or "items" not in data:
        await call.answer("⚠️ حدث خطأ أو لا توجد تعقيبات.", show_alert=True)
        return

    items = data["items"]
    per_page = 5
    total_pages = max(1, (len(items) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))

    start_idx = page * per_page
    chunk = items[start_idx:start_idx + per_page]

    text = format_taqibat_page(chunk, prayer_names.get(prayer, prayer), page, total_pages)
    kb = taqibat_pagination_keyboard(prayer, page, total_pages)

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()


# ═══════════════════════════════════════════════════════════
# LIBRARY CALLBACKS
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "library:duas")
async def callback_library_duas(call: CallbackQuery):
    items = get_all_items("daily_dua")
    kb = pagination_buttons(items, "dua_lib", page=0, per_page=5) if items else library_duas_menu()
    await call.message.edit_text(
        "🤲 <b>الأدعية</b>\n\nاختر دعاء أو اضغط عشوائي:",
        reply_markup=kb, parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "library:ziyarat")
async def callback_library_ziyarat(call: CallbackQuery):
    items = get_all_items("ziyarat")
    kb = pagination_buttons(items, "ziyarat_lib", page=0, per_page=5) if items else library_ziyarat_menu()
    await call.message.edit_text(
        "🕌 <b>الزيارات</b>\n\nاختر زيارة أو اضغط عشوائي:",
        reply_markup=kb, parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "library:munajat")
async def callback_library_munajat(call: CallbackQuery):
    items = get_all_items("munajat")
    kb = pagination_buttons(items, "munajat_lib", page=0, per_page=5) if items else library_munajat_menu()
    await call.message.edit_text(
        "✨ <b>المناجيات</b>\n\nاختر مناجاة أو اضغط عشوائي:",
        reply_markup=kb, parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "library:hadith")
async def callback_library_hadith(call: CallbackQuery):
    items = get_all_items("hadith")
    kb = pagination_buttons(items, "hadith_lib", page=0, per_page=5) if items else back_button("menu:library")
    await call.message.edit_text(
        "📖 <b>الأحاديث</b>\n\nاختر حديثاً:",
        reply_markup=kb, parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "library:wisdom")
async def callback_library_wisdom(call: CallbackQuery):
    items = get_all_items("wisdom_featured") or get_all_items("wisdom_short")
    kb = pagination_buttons(items, "wisdom_lib", page=0, per_page=5) if items else back_button("menu:library")
    await call.message.edit_text(
        "💎 <b>الحكم</b>\n\nاختر حكمة:",
        reply_markup=kb, parse_mode="HTML"
    )
    await call.answer()


# ═══════════════════════════════════════════════════════════
# RANDOM CONTENT CALLBACKS
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "dua:random")
async def callback_random_dua(call: CallbackQuery):
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


@router.callback_query(F.data == "ziyarat:random")
async def callback_random_ziyarat(call: CallbackQuery):
    user_id = call.from_user.id
    item = get_random_item("ziyarat", user_id)

    if not item:
        await call.answer("🕌 عذراً، لم يتم العثور على زيارة حالياً.", show_alert=True)
        return

    db.mark_content_sent(user_id, "ziyarat", item["id"])

    if item.get("is_pdf") and item.get("file_id"):
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer_document(
            document=item["file_id"],
            caption=f"🕌 <b>{item.get('title', 'زيارة')}</b>\n\nنسألكم الدعاء 🤲",
            parse_mode="HTML"
        )
        await call.answer("تم إرسال ملف الزيارة ✅")
    else:
        text = format_ziyarat(item) if item.get("text") else "🕌 لا يوجد محتوى متوفر حالياً."
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:library"))
        await call.answer()


@router.callback_query(F.data == "munajat:random")
async def callback_random_munajat(call: CallbackQuery):
    item = get_random_item("munajat", call.from_user.id)
    if item:
        db.mark_content_sent(call.from_user.id, "munajat", item["id"])
        text = format_munajat(item)
    else:
        text = "✨ لا يوجد محتوى متوفر حالياً."

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:library"))
    await call.answer()
