"""
handlers/prayer.py — أوقات الصلاة، GPS، اختيار المدينة والموقع
"""

import logging

from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
)

import config
import database as db
from services.prayer_service import (
    get_prayer_times, get_next_prayer,
    format_prayer_times, format_next_prayer,
)
from services.navigation_service import (
    prayer_menu, taqibat_menu, back_button,
    location_settings_menu, governorates_keyboard, districts_keyboard,
)
from services.location_data import IRAQ_CITIES

logger = logging.getLogger(__name__)
router = Router(name="prayer_router")


# ═══════════════════════════════════════════════════════════
# HELPER
# ═══════════════════════════════════════════════════════════

async def send_prayer_times(message_or_call):
    user = db.get_user(message_or_call.from_user.id)
    if user:
        times = await get_prayer_times(
            user.get("latitude", config.LATITUDE),
            user.get("longitude", config.LONGITUDE),
            user.get("timezone", config.TIMEZONE),
            user.get("city", config.CITY)
        )
    else:
        times = await get_prayer_times(config.LATITUDE, config.LONGITUDE, config.TIMEZONE, config.CITY)

    text = format_prayer_times(times, user.get("city", config.CITY) if user else config.CITY)

    if isinstance(message_or_call, CallbackQuery):
        await message_or_call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:prayer"))
        await message_or_call.answer()
    else:
        await message_or_call.answer(text, parse_mode="HTML")


# ═══════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════

@router.message(Command("prayer"))
async def cmd_prayer(message: Message):
    await send_prayer_times(message)


@router.message(Command("city"))
async def cmd_city(message: Message, command: CommandObject):
    args = command.args
    if not args:
        await message.answer(
            "🕌 أرسل اسم المدينة:\n<code>/city اسم_المدينة</code>",
            parse_mode="HTML"
        )
        return

    city_name = args.strip()
    city_coords = {
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
        "طهران":               (35.6892, 51.3890),
        "قم":                  (34.6401, 50.8764),
        "مشهد":                (36.2605, 59.6168),
        "أصفهان":              (32.6539, 51.6660),
        "اصفهان":              (32.6539, 51.6660),
        "شيراز":               (29.5926, 52.5836),
        "تبريز":               (38.0800, 46.2919),
        "اهواز":               (31.3183, 48.6706),
        "الأهواز":             (31.3183, 48.6706),
        "مكة":                 (21.3891, 39.8579),
        "مكة المكرمة":         (21.3891, 39.8579),
        "المدينة":             (24.5247, 39.5692),
        "المدينة المنورة":     (24.5247, 39.5692),
        "الرياض":              (24.6877, 46.7219),
        "جدة":                 (21.4858, 39.1925),
        "الدمام":              (26.4207, 50.0888),
        "القطيف":              (26.5296, 50.0055),
        "الكويت":              (29.3759, 47.9774),
        "مدينة الكويت":        (29.3759, 47.9774),
        "المنامة":             (26.2154, 50.5832),
        "بيروت":               (33.8938, 35.5018),
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


# ═══════════════════════════════════════════════════════════
# PRAYER CALLBACKS
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "prayer:times")
async def callback_prayer_times(call: CallbackQuery):
    await send_prayer_times(call)


@router.callback_query(F.data == "prayer:next")
async def callback_prayer_next(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    if user:
        info = await get_next_prayer(
            user.get("latitude", config.LATITUDE),
            user.get("longitude", config.LONGITUDE),
            user.get("timezone", config.TIMEZONE),
            user.get("city", config.CITY)
        )
    else:
        info = await get_next_prayer(config.LATITUDE, config.LONGITUDE, config.TIMEZONE, config.CITY)

    text = format_next_prayer(info)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:prayer"))
    await call.answer()


@router.callback_query(F.data == "prayer:taqibat")
async def callback_prayer_taqibat(call: CallbackQuery):
    await call.message.edit_text(
        "📿 <b>تعقيبات الصلاة</b>\n\nاختر الصلاة:",
        reply_markup=taqibat_menu(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "prayer:reminder")
async def callback_prayer_reminder(call: CallbackQuery):
    text = (
        "🔔 <b>تذكير الصلاة</b>\n\n"
        "يمكنك تفعيل تذكير الصلاة من خلال:\n"
        "الإعدادات ➜ اشتراكاتي ➜ تذكير الصلاة\n\n"
        "سيصلك إشعار عند دخول وقت كل صلاة\n"
        "مع الأذكار والتعقيبات المستحبة."
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:settings"))
    await call.answer()


# ═══════════════════════════════════════════════════════════
# LOCATION / GPS CALLBACKS
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "settings:city")
async def callback_settings_city(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    current_city = user.get("city", config.CITY) if user else config.CITY
    current_lat  = user.get("latitude",  config.LATITUDE)  if user else config.LATITUDE
    current_lng  = user.get("longitude", config.LONGITUDE) if user else config.LONGITUDE

    text = (
        "📍 <b>إعداد الموقع الجغرافي</b>\n\n"
        f"📌 <b>موقعك الحالي:</b> {current_city}\n"
        f"🌐 الإحداثيات: {current_lat:.4f}, {current_lng:.4f}\n\n"
        "اختر طريقة تحديث الموقع:\n\n"
        "📡 <b>GPS (موصى به):</b> دقة تامة بناءً على موقعك الفعلي.\n"
        "🗺 <b>يدوي:</b> اختر محافظتك وقضاءك من القائمة."
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=location_settings_menu())
    await call.answer()


@router.callback_query(F.data == "location:request_gps")
async def callback_location_request_gps(call: CallbackQuery):
    await call.answer()

    gps_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 مشاركة موقعي الحالي", request_location=True)],
            [KeyboardButton(text="🔙 إلغاء")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    try:
        await call.message.answer(
            "📡 <b>مشاركة الموقع عبر GPS</b>\n\n"
            "اضغط الزر أدناه لمشاركة موقعك الحالي.\n"
            "سيُستخدم موقعك لحساب مواقيت الصلاة بدقة تامة.\n\n"
            "⚠️ <i>تأكد من تفعيل خدمة الموقع (GPS) في جهازك وإعطاء تطبيق تيليغرام إذن الوصول إليه.</i>",
            parse_mode="HTML",
            reply_markup=gps_kb,
        )
    except Exception as e:
        logger.error(f"[GPS] فشل إرسال رسالة GPS: {e}")


@router.callback_query(F.data == "location:manual")
async def callback_location_manual(call: CallbackQuery):
    await call.message.edit_text(
        "🗺 <b>اختيار المحافظة</b>\n\nاختر محافظتك من القائمة:",
        parse_mode="HTML",
        reply_markup=governorates_keyboard(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("location:gov:"))
async def callback_location_governorate(call: CallbackQuery):
    governorate = call.data.split("location:gov:", 1)[1]
    if governorate not in IRAQ_CITIES:
        await call.answer("⚠️ محافظة غير موجودة", show_alert=True)
        return

    await call.message.edit_text(
        f"🗺 <b>محافظة {governorate}</b>\n\nاختر القضاء:",
        parse_mode="HTML",
        reply_markup=districts_keyboard(governorate),
    )
    await call.answer()


@router.callback_query(F.data.startswith("location:district:"))
async def callback_location_district(call: CallbackQuery):
    parts = call.data.split(":", 3)
    if len(parts) < 4:
        await call.answer("⚠️ بيانات غير صحيحة", show_alert=True)
        return

    governorate = parts[2]
    district_safe = parts[3]
    district = district_safe.replace("_", ":")

    coords = IRAQ_CITIES.get(governorate, {}).get(district)
    if not coords:
        await call.answer("⚠️ القضاء غير موجود", show_alert=True)
        return

    lat = coords["lat"]
    lng = coords["lng"]
    city_label = f"{governorate} - {district}"

    db.update_user_location(call.from_user.id, city_label, lat, lng)

    await call.message.edit_text(
        f"✅ <b>تم تحديث موقعك بنجاح!</b>\n\n"
        f"📌 <b>المنطقة:</b> {city_label}\n"
        f"🌐 الإحداثيات: {lat:.4f}, {lng:.4f}\n\n"
        f"ستعتمد مواقيت الصلاة الآن على هذا الموقع.",
        parse_mode="HTML",
        reply_markup=back_button("menu:settings"),
    )
    await call.answer("✅ تم حفظ الموقع")


# ═══════════════════════════════════════════════════════════
# GPS MESSAGE HANDLERS
# ═══════════════════════════════════════════════════════════

@router.message(F.location)
async def handle_user_location(message: Message):
    lat = message.location.latitude
    lng = message.location.longitude
    user_id = message.from_user.id

    try:
        success = db.update_user_location(user_id, "موقعي المخصص (GPS)", lat, lng)

        if success:
            await message.answer(
                f"✅ <b>تم تحديث موقعك بنجاح!</b>\n\n"
                f"📍 <b>الإحداثيات المستلمة:</b>\n"
                f"• خط العرض: {lat:.5f}\n"
                f"• خط الطول: {lng:.5f}\n\n"
                f"ستعتمد مواقيت الصلاة الآن على موقعك الفعلي بدقة تامة. 🕌",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove(),
            )
        else:
            await message.answer(
                "⚠️ لم يتم التعرف على حسابك. الرجاء إرسال /start أولاً ثم إعادة المحاولة.",
                reply_markup=ReplyKeyboardRemove(),
            )
    except Exception as e:
        logger.error(f"[GPS LOCATION] خطأ في معالجة موقع المستخدم {user_id}: {e}")
        try:
            await message.answer(
                "⚠️ حدث خطأ أثناء حفظ الموقع. الرجاء المحاولة مرة أخرى.",
                reply_markup=ReplyKeyboardRemove(),
            )
        except Exception:
            pass


@router.message(F.text == "🔙 إلغاء")
async def handle_gps_cancel(message: Message):
    await message.answer(
        "🔙 تم الإلغاء. يمكنك تغيير الموقع في أي وقت من الإعدادات.",
        reply_markup=ReplyKeyboardRemove(),
    )
