"""
handlers/events.py — المناسبات الدينية والتقويم الهجري
"""

import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from services.event_service import (
    get_today_event, get_upcoming_events,
    get_today_hijri, format_hijri_date, format_event,
    format_upcoming_events, get_hijri_calendar,
)
from services.navigation_service import back_button, events_menu

logger = logging.getLogger(__name__)
router = Router(name="events_router")


@router.message(Command("event"))
async def cmd_event(message: Message):
    event = get_today_event()
    if event:
        await message.answer(format_event(event), parse_mode="HTML")
    else:
        await message.answer("📅 لا توجد مناسبة خاصة اليوم.")


@router.callback_query(F.data == "event:today")
async def callback_event_today(call: CallbackQuery):
    event = get_today_event()
    if event:
        text = format_event(event)
    else:
        hijri = get_today_hijri()
        text = (
            f"📅 <b>مناسبة اليوم</b>\n\n"
            f"📆 {format_hijri_date(hijri)}\n\n"
            "لا توجد مناسبة خاصة بهذا اليوم.\n\n"
            "تفقد المناسبات القادمة من القائمة. 🌹"
        )

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:events"))
    await call.answer()


@router.callback_query(F.data == "event:upcoming")
async def callback_event_upcoming(call: CallbackQuery):
    events = get_upcoming_events(days=30)
    text = format_upcoming_events(events)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:events"))
    await call.answer()


@router.callback_query(F.data == "event:works")
async def callback_event_works(call: CallbackQuery):
    event = get_today_event()
    if event and event.get("amal"):
        text = f"✨ <b>أعمال {event.get('title', 'المناسبة')}</b>\n\n{event['amal']}"
    else:
        text = (
            "✨ <b>أعمال المناسبة</b>\n\n"
            "من الأعمال المستحبة بشكل عام:\n\n"
            "• الصيام\n"
            "• الصلاة على محمد وآل محمد\n"
            "• الدعاء بالمأثورات\n"
            "• زيارة الإمام الحسين عليه السلام\n"
            "• قراءة القرآن الكريم\n"
            "• الصدقة\n"
            "• الاستغفار\n\n"
            "📅 تفقد مناسبة اليوم لمعرفة الأعمال الخاصة بها."
        )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:events"))
    await call.answer()


@router.callback_query(F.data == "event:calendar")
async def callback_event_calendar(call: CallbackQuery):
    text = get_hijri_calendar()
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("menu:events"))
    await call.answer()
