"""
Athar Shia Bot - Event Service
بوت آثار الشيعة - خدمة المناسبات
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from hijri_converter import convert

DATA_DIR = Path(__file__).parent.parent / "data" / "normalized"


def load_json(filepath: Path) -> Dict:
    """Load JSON file."""
    if not filepath.exists():
        return {"items": []}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"items": []}


def get_today_hijri() -> Dict[str, int]:
    """Get today's Hijri date."""
    today = datetime.now()
    hijri = convert.Gregorian(today.year, today.month, today.day).to_hijri()
    return {
        "year": hijri.year,
        "month": hijri.month,
        "day": hijri.day,
        "month_name": get_hijri_month_name(hijri.month)
    }


def get_hijri_month_name(month: int) -> str:
    """Get Hijri month name in Arabic."""
    months = {
        1: "محرم", 2: "صفر", 3: "ربيع الأول", 4: "ربيع الثاني",
        5: "جمادى الأولى", 6: "جمادى الآخرة", 7: "رجب", 8: "شعبان",
        9: "رمضان", 10: "شوال", 11: "ذو القعدة", 12: "ذو الحجة"
    }
    return months.get(month, "")


def _parse_hijri_date(item: Dict) -> tuple:
    """
    Parse the hijri date from an event item.
    Supports two formats:
      - hijri_date: "DD-MM"  (migrated format: day-month)
      - month + day as separate integer fields (old format)
    Returns (month, day) as integers.
    """
    hijri_date = item.get("hijri_date", "")
    if hijri_date and "-" in str(hijri_date):
        parts = str(hijri_date).split("-")
        try:
            day = int(parts[0])
            month = int(parts[1])
            return month, day
        except (ValueError, IndexError):
            pass
    return item.get("month", 0), item.get("day", 0)


def get_today_event() -> Optional[Dict[str, Any]]:
    """Get today's event if any."""
    hijri = get_today_hijri()
    filepath = DATA_DIR / "event_content" / "events.json"
    data = load_json(filepath)

    for item in data.get("items", []):
        month, day = _parse_hijri_date(item)
        if month == hijri["month"] and day == hijri["day"]:
            return item
    return None


def get_upcoming_events(days: int = 30) -> List[Dict[str, Any]]:
    """Get upcoming events within N days."""
    hijri = get_today_hijri()
    filepath = DATA_DIR / "event_content" / "events.json"
    data = load_json(filepath)

    current_day = hijri["month"] * 30 + hijri["day"]
    upcoming = []

    for item in data.get("items", []):
        month, day = _parse_hijri_date(item)
        item_day = month * 30 + day
        diff = item_day - current_day
        if 0 <= diff <= days:
            item_copy = dict(item)
            item_copy["days_until"] = diff
            item_copy["_month"] = month
            item_copy["_day"] = day
            upcoming.append(item_copy)

    return sorted(upcoming, key=lambda x: x.get("days_until", 0))


def get_weekly_dua() -> Optional[Dict[str, Any]]:
    """Get dua for the current weekday."""
    weekday = datetime.now().strftime("%A").lower()
    filepath = DATA_DIR / "event_content" / "weekly_duas.json"
    data = load_json(filepath)

    for item in data.get("items", []):
        if item.get("weekday", "").lower() == weekday:
            return item
    return None


def get_event_by_date(month: int, day: int) -> Optional[Dict[str, Any]]:
    """Get event by specific Hijri date."""
    filepath = DATA_DIR / "event_content" / "events.json"
    data = load_json(filepath)

    for item in data.get("items", []):
        m, d = _parse_hijri_date(item)
        if m == month and d == day:
            return item
    return None


def format_hijri_date(hijri: Dict) -> str:
    """Format Hijri date for display."""
    return f"{hijri['day']} {hijri['month_name']} {hijri['year']} هـ"


def format_event(event: Dict) -> str:
    """Format event for display."""
    title = event.get("title", "")
    description = event.get("description", "")
    amal = event.get("amal", "")
    month, day = _parse_hijri_date(event)
    is_happy = event.get("is_happy", False)
    is_sad = event.get("is_sad", False)

    emoji = "🎉" if is_happy else "⚫" if is_sad else "📌"

    result = f"{emoji} <b>{title}</b>\n"
    result += f"📅 {day} {get_hijri_month_name(month)}\n\n"

    if description:
        result += f"{description}\n\n"

    if amal:
        result += f"✨ <b>الأعمال المستحبة:</b>\n{amal}"

    return result


def format_upcoming_events(events: List[Dict]) -> str:
    """Format upcoming events list."""
    result = "📅 <b>المناسبات القادمة</b>\n\n"

    if not events:
        result += "لا توجد مناسبات قادمة."
        return result

    for event in events:
        days = event.get("days_until", 0)
        title = event.get("title", "")
        month = event.get("_month", 0)
        day = event.get("_day", 0)

        if days == 0:
            result += f"• 📌 <b>{title}</b> - اليوم!\n"
        else:
            result += f"• {title} - بعد {days} يوم ({day} {get_hijri_month_name(month)})\n"

    return result


def format_weekly_dua(dua: Dict) -> str:
    """Format weekly dua for display."""
    title = dua.get("title", "")
    text = dua.get("text", "")
    file_id = dua.get("file_id", "")

    result = f"🤲 <b>{title}</b>\n\n"
    if text:
        result += f"{text}\n\n"
    if file_id:
        result += "📎 يمكنك تحميل الملف الكامل من المكتبة."

    return result


def get_hijri_calendar(year: Optional[int] = None) -> str:
    """Get Hijri calendar overview."""
    hijri = get_today_hijri()
    if year is None:
        year = hijri["year"]

    result = f"🗓 <b>التقويم الهجري {year} هـ</b>\n\n"

    months_data = {
        1: ("محرم", "📌"),
        2: ("صفر", "📌"),
        3: ("ربيع الأول", "🎉"),
        4: ("ربيع الثاني", "🎉"),
        5: ("جمادى الأولى", "📌"),
        6: ("جمادى الآخرة", "📌"),
        7: ("رجب", "🌟"),
        8: ("شعبان", "🌟"),
        9: ("رمضان", "🌙"),
        10: ("شوال", "🎉"),
        11: ("ذو القعدة", "📌"),
        12: ("ذو الحجة", "🕋"),
    }

    for m, (name, emoji) in months_data.items():
        result += f"{emoji} {m}. {name}\n"

    result += f"\n📅 اليوم: {format_hijri_date(hijri)}"
    return result
