"""
Athar Shia Bot - Event Service
بوت آثار الشيعة - خدمة المناسبات

حساب المناسبات يعتمد على ترتيب يومي حقيقي داخل السنة الهجرية
باستخدام أطوال الشهور الهجرية الفعلية.
"""

import json
import re
from datetime import datetime, timedelta
from hijri_converter import convert
import config
from pathlib import Path
from typing import Optional, Dict, Any, List

from hijri_converter import convert

DATA_DIR = Path(__file__).parent.parent / "data" / "normalized"

# ── أطوال الشهور الهجرية الفعلية (30-29 بالتناوب، ذو الحجة 29) ──
HIJRI_MONTH_LENGTHS = [30, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29]
TOTAL_HIJRI_YEAR_DAYS = sum(HIJRI_MONTH_LENGTHS)  # 354

# الموقع الترتيبي لأول يوم من كل شهر داخل السنة (1-based)
_MONTH_START_ORDINAL = []
_pos = 1
for _L in HIJRI_MONTH_LENGTHS:
    _MONTH_START_ORDINAL.append(_pos)
    _pos += _L


def load_json(filepath: Path) -> Dict:
    if not filepath.exists():
        return {"items": []}
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"items": []}


# ─────────────────────────────────────────────
# التاريخ الهجري
# ─────────────────────────────────────────────

def get_today_hijri() -> Dict[str, int]:
    # جلب الوقت الحالي
    today_geo = datetime.now()

    # تطبيق إزاحة التاريخ من الإعدادات
    adjusted_geo = today_geo + timedelta(days=config.HIJRI_OFFSET)

    # تحويل التاريخ المعدل إلى هجري
    h = convert.Gregorian(adjusted_geo.year, adjusted_geo.month, adjusted_geo.day).to_hijri()

    return {
        "year":       h.year,
        "month":      h.month,
        "day":        h.day,
        "month_name": get_hijri_month_name(h.month),
    }


def get_hijri_month_name(month: int) -> str:
    months = {
        1: "محرم",   2: "صفر",       3: "ربيع الأول",  4: "ربيع الثاني",
        5: "جمادى الأولى", 6: "جمادى الآخرة", 7: "رجب",  8: "شعبان",
        9: "رمضان",  10: "شوال",     11: "ذو القعدة",   12: "ذو الحجة",
    }
    return months.get(month, "")


# ─────────────────────────────────────────────
# حساب الترتيب اليومي داخل السنة الهجرية
# ─────────────────────────────────────────────

def hijri_day_ordinal(month: int, day: int) -> int:
    """
    يحوّل (month, day) إلى رقم ترتيبي داخل السنة الهجرية.
    مثال: (1,1)=1  (1,10)=10  (2,1)=31  (12,29)=354
    """
    if not (1 <= month <= 12):
        return 0
    return _MONTH_START_ORDINAL[month - 1] + (day - 1)


def days_until_event(event_month: int, event_day: int,
                     current_month: int, current_day: int) -> int:
    """
    يحسب عدد الأيام حتى المناسبة القادمة مع دعم الانتقال للسنة التالية.
    """
    ev_ord  = hijri_day_ordinal(event_month, event_day)
    cur_ord = hijri_day_ordinal(current_month, current_day)
    diff = ev_ord - cur_ord
    if diff < 0:
        diff += TOTAL_HIJRI_YEAR_DAYS
    return diff


# ─────────────────────────────────────────────
# تحليل حقل hijri_date  (صيغة DD-MM)
# ─────────────────────────────────────────────

def _parse_hijri_date(item: Dict) -> tuple:
    """
    يُرجع (month, day) كأعداد صحيحة.
    الصيغة المخزنة: "DD-MM"  (يوم-شهر)
    """
    hijri_date = item.get("hijri_date", "")
    if hijri_date and "-" in str(hijri_date):
        parts = str(hijri_date).split("-")
        try:
            day   = int(parts[0])
            month = int(parts[1])
            return month, day
        except (ValueError, IndexError):
            pass
    # fallback: حقول month/day منفصلة (صيغة قديمة)
    return item.get("month", 0), item.get("day", 0)


# ─────────────────────────────────────────────
# واجهة البيانات
# ─────────────────────────────────────────────

def get_today_event() -> Optional[Dict[str, Any]]:
    """Get event for today based on adjusted Hijri date."""
    hijri = get_today_hijri()
    day_num = int(hijri["day"])
    month_num = int(hijri["month"])

    data = load_json(DATA_DIR / "event_content" / "events.json")

    for item in data.get("items", []):
        # محاولة قراءة اليوم والشهر كأرقام من الملف مباشرة لتجنب أخطاء النص
        try:
            item_day = int(item.get("day", 0))
            # إذا كان الشهر مكتوباً كنص أو رقم، نحاول استخراجه من hijri_date (القسم الثاني بعد الشارطة)
            hijri_date_parts = item.get("hijri_date", "").split("-")
            item_month = int(hijri_date_parts[1]) if len(hijri_date_parts) > 1 else int(item.get("month", 0))

            if item_day == day_num and item_month == month_num:
                return item
        except (ValueError, IndexError):
            continue

    return None

def get_today_events_list(date_dt: datetime) -> List[Dict[str, Any]]:
    """Get list of events for a specific date (used by scheduler)."""
    # نقوم بنفس العملية البرمجية الآمنة هنا أيضاً
    h = convert.Gregorian(date_dt.year, date_dt.month, date_dt.day).to_hijri()
    day_num = int(h.day)
    month_num = int(h.month)

    data = load_json(DATA_DIR / "events.json")
    events = []

    for item in data.get("items", []):
        try:
            item_day = int(item.get("day", 0))
            hijri_date_parts = item.get("hijri_date", "").split("-")
            item_month = int(hijri_date_parts[1]) if len(hijri_date_parts) > 1 else int(item.get("month", 0))

            if item_day == day_num and item_month == month_num:
                events.append(item)
        except (ValueError, IndexError):
            continue

    return events


def get_upcoming_events(days: int = 30) -> List[Dict[str, Any]]:
    """
    يُرجع المناسبات خلال N يوماً القادمة.
    يستخدم الترتيب اليومي الحقيقي مع دعم عبور نهاية السنة.
    """
    hijri = get_today_hijri()
    data  = load_json(DATA_DIR / "event_content" / "events.json")

    cur_m, cur_d = hijri["month"], hijri["day"]
    upcoming = []

    for item in data.get("items", []):
        ev_m, ev_d = _parse_hijri_date(item)
        if not ev_m or not ev_d:
            continue
        diff = days_until_event(ev_m, ev_d, cur_m, cur_d)
        if 0 < diff <= days:          # 0 = اليوم نفسه (يُعرض عبر get_today_event)
            copy = dict(item)
            copy["days_until"] = diff
            copy["_month"]     = ev_m
            copy["_day"]       = ev_d
            upcoming.append(copy)

    return sorted(upcoming, key=lambda x: x["days_until"])



def get_weekly_dua() -> Optional[Dict[str, Any]]:
    weekday = datetime.now().strftime("%A").lower()
    data    = load_json(DATA_DIR / "event_content" / "weekly_duas.json")
    for item in data.get("items", []):
        if item.get("weekday", "").lower() == weekday:
            return item
    return None


def get_weekly_ziyarat() -> Optional[Dict[str, Any]]:
    weekday = datetime.now().strftime("%A").lower()
    data    = load_json(DATA_DIR / "event_content" / "weekly_ziyarat.json")
    for item in data.get("items", []):
        if item.get("weekday", "").lower() == weekday:
            return item
    return None


def get_event_by_date(month: int, day: int) -> Optional[Dict[str, Any]]:
    data = load_json(DATA_DIR / "event_content" / "events.json")
    for item in data.get("items", []):
        m, d = _parse_hijri_date(item)
        if m == month and d == day:
            return item
    return None


# ─────────────────────────────────────────────
# تنسيق العرض
# ─────────────────────────────────────────────

def format_hijri_date(hijri: Dict) -> str:
    return f"{hijri['day']} {hijri['month_name']} {hijri['year']} هـ"


def format_event(event: Dict) -> str:
    text  = event.get("text", "")
    month_name = event.get("month", "")
    day   = event.get("day", "")
    m, d  = _parse_hijri_date(event)
    if not month_name:
        month_name = get_hijri_month_name(m)

    result  = f"📅 <b>{d} {month_name}</b>\n\n"
    result += text[:3800]
    if len(text) > 3800:
        result += "\n\n<i>... (يتبع)</i>"
    return result


def format_upcoming_events(events: List[Dict]) -> str:
    result = "📅 <b>المناسبات القادمة</b>\n\n"
    if not events:
        result += "لا توجد مناسبات في الأيام القادمة."
        return result

    for event in events:
        days   = event.get("days_until", 0)
        month  = event.get("_month", 0)
        day    = event.get("_day", 0)
        month_name = get_hijri_month_name(month)
        text_preview = event.get("text", "")

        # 1. استخراج أول سطر
        first_line = text_preview.split("\n")[0].lstrip("* ").strip()

        # 2. تنظيف السطر من أي وسوم HTML لتجنب كسر التنسيق عند القص
        clean_line = re.sub(r'<[^>]+>', '', first_line)

        # 3. قص النص الآمن
        title = clean_line[:60] + "…" if len(clean_line) > 60 else clean_line

        result += f"• <b>{day} {month_name}</b> — بعد {days} يوم\n"
        result += f"  <i>{title}</i>\n\n"

    return result.rstrip()


def format_weekly_dua(dua: Dict) -> str:
    title   = dua.get("title", "")
    text    = dua.get("text", "")
    result  = f"🤲 <b>{title}</b>\n\n"
    if text:
        result += f"{text}\n\n"
    return result


def get_hijri_calendar(year: Optional[int] = None) -> str:
    hijri = get_today_hijri()
    if year is None:
        year = hijri["year"]
    result = f"🗓 <b>التقويم الهجري {year} هـ</b>\n\n"
    months_info = [
        (1,  "محرم",            "📌"),
        (2,  "صفر",             "📌"),
        (3,  "ربيع الأول",      "🎉"),
        (4,  "ربيع الثاني",     "🎉"),
        (5,  "جمادى الأولى",    "📌"),
        (6,  "جمادى الآخرة",    "📌"),
        (7,  "رجب",             "🌟"),
        (8,  "شعبان",           "🌟"),
        (9,  "رمضان",           "🌙"),
        (10, "شوال",            "🎉"),
        (11, "ذو القعدة",       "📌"),
        (12, "ذو الحجة",        "🕋"),
    ]
    for m, name, emoji in months_info:
        result += f"{emoji} {m}. {name}\n"
    result += f"\n📅 اليوم: {format_hijri_date(hijri)}"
    return result
