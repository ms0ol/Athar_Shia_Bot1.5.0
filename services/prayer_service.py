"""
Athar Shia Bot - Prayer Service
بوت أثَر الشيعة - خدمة الصلاة والأذان
"""

import math
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import database as db


# ─── Prayer Time Calculations ───

class PrayerCalculator:
    """Calculate prayer times using Jafari/Shia method."""

    def __init__(self, lat: float, lng: float, timezone: str = "Asia/Baghdad"):
        self.lat = lat
        self.lng = lng
        self.timezone_offset = self._get_timezone_offset(timezone)

    def _get_timezone_offset(self, timezone: str) -> float:
        """Get timezone offset from UTC in hours."""
        tz_offsets = {
            "Asia/Baghdad": 3.0,
            "Asia/Tehran": 3.5,
            "Asia/Qum": 3.5,
            "Asia/Dubai": 4.0,
            "Asia/Kuwait": 3.0,
            "Asia/Riyadh": 3.0,
            "Asia/Qatar": 3.0,
            "Asia/Bahrain": 3.0,
            "Asia/Beirut": 3.0,
            "Asia/Damascus": 3.0,
            "Asia/Amman": 3.0,
            "Asia/Jerusalem": 3.0,
            "Africa/Cairo": 2.0,
            "Asia/Karachi": 5.0,
            "Asia/Kolkata": 5.5,
            "Europe/Istanbul": 3.0,
            "UTC": 0.0,
        }
        return tz_offsets.get(timezone, 3.0)

    def _jday(self, date: datetime) -> float:
        """Convert Gregorian date to Julian day."""
        y = date.year
        m = date.month
        d = date.day

        if m <= 2:
            y -= 1
            m += 12

        a = math.floor(y / 100)
        b = 2 - a + math.floor(a / 4)

        jd = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5
        return jd

    def _sun_position(self, jd: float) -> Tuple[float, float]:
        """Calculate sun declination and equation of time."""
        d = jd - 2451545.0

        # Mean longitude of the sun
        L = (280.460 + 0.9856474 * d) % 360.0
        if L < 0:
            L += 360.0

        # Mean anomaly of the sun
        g = (357.528 + 0.9856003 * d) % 360.0
        if g < 0:
            g += 360.0

        # Convert to radians
        g_rad = math.radians(g)

        # Ecliptic longitude
        ecliptic_longitude = L + 1.915 * math.sin(g_rad) + 0.020 * math.sin(2 * g_rad)
        ecliptic_longitude_rad = math.radians(ecliptic_longitude)

        # Obliquity of the ecliptic
        epsilon = 23.439 - 0.0000004 * d
        epsilon_rad = math.radians(epsilon)

        # Right ascension and declination
        ra = math.degrees(math.atan2(
            math.cos(epsilon_rad) * math.sin(ecliptic_longitude_rad),
            math.cos(ecliptic_longitude_rad)
        ))
        if ra < 0:
            ra += 360.0

        decl = math.degrees(math.asin(
            math.sin(epsilon_rad) * math.sin(ecliptic_longitude_rad)
        ))

        # Equation of time in minutes
        eqt = 4 * (L - ra)

        return decl, eqt

    def _compute_time(self, angle: float, decl: float, eqt: float, is_night: bool = False) -> float:
        """Compute prayer time for a given sun horizon altitude angle (degrees)."""
        lat_rad = math.radians(self.lat)
        decl_rad = math.radians(decl)

        # Standard Islamic prayer formula: cos_H = (sin(a) - sin(φ)·sin(δ)) / (cos(φ)·cos(δ))
        cos_h = (math.sin(math.radians(angle)) - math.sin(lat_rad) * math.sin(decl_rad)) / \
                (math.cos(lat_rad) * math.cos(decl_rad))

        cos_h = max(-1.0, min(1.0, cos_h))
        h = math.degrees(math.acos(cos_h))

        # is_night=True → event is before noon (subtract hour angle)
        if is_night:
            h = -h

        t = 12.0 + (h / 15.0) - (eqt / 60.0) - (self.lng / 15.0) + self.timezone_offset
        return t

    def calculate_times(self, date: datetime) -> Dict[str, str]:
        """Calculate all prayer times for a given date."""
        jd = self._jday(date)
        decl, eqt = self._sun_position(jd)

        # Jafari/Shia method (مذهب الإمامية الاثني عشرية)
        times = {}

        # Fajr: true dawn angle -16° (Ja'fari/Iraq standard)
        fajr_time = self._compute_time(-16.0, decl, eqt, is_night=True)
        times["fajr"] = self._format_time(fajr_time)

        # Sunrise: solar altitude -0.833° (standard refraction)
        sunrise_time = self._compute_time(-0.833, decl, eqt, is_night=True)
        times["sunrise"] = self._format_time(sunrise_time)

        # Dhuhr: true noon (sun crosses meridian)
        dhuhr_time = 12.0 - (eqt / 60.0) - (self.lng / 15.0) + self.timezone_offset
        times["dhuhr"] = self._format_time(dhuhr_time)

        # Asr: Ja'fari/Shia = shadow length equals 2× object height (مذهب الحنفي الثاني)
        lat_rad = math.radians(self.lat)
        decl_rad = math.radians(decl)
        noon_alt = 90.0 - abs(self.lat - decl)
        asr_angle = math.degrees(math.atan(1.0 / (2.0 + 1.0 / math.tan(math.radians(noon_alt)))))
        asr_time = self._compute_time(asr_angle, decl, eqt, is_night=False)
        times["asr"] = self._format_time(asr_time)

        # Sunset (for reference)
        sunset_time = self._compute_time(-0.833, decl, eqt, is_night=False)
        times["sunset"] = self._format_time(sunset_time)

        # Maghrib (Ja'fari): disappearance of redness from eastern sky ≈ sunset + ~17min
        # Modeled as solar altitude -4° after sunset
        maghrib_time = self._compute_time(-4.0, decl, eqt, is_night=False)
        times["maghrib"] = self._format_time(maghrib_time)

        # Isha: disappearance of evening twilight glow, angle -14° (Ja'fari standard)
        isha_time = self._compute_time(-14.0, decl, eqt, is_night=False)
        times["isha"] = self._format_time(isha_time)

        # Midnight (Shia): halfway between Maghrib and next day's Fajr
        fajr_next = fajr_time + 24.0
        midnight_time = (maghrib_time + fajr_next) / 2.0
        times["midnight"] = self._format_time(midnight_time % 24)

        return times

    def _format_time(self, hours: float) -> str:
        """Convert decimal hours to HH:MM format."""
        hours = hours % 24
        h = int(hours)
        m = int((hours - h) * 60)
        return f"{h:02d}:{m:02d}"


# ─── Service Functions ───

def get_prayer_times(lat: float, lng: float, timezone: str, city: str) -> Dict[str, str]:
    """Get prayer times with caching."""
    today = datetime.now().strftime("%Y-%m-%d")

    # Check cache
    cached = db.get_cached_prayer_times(today, city)
    if cached:
        return cached

    # Calculate
    calc = PrayerCalculator(lat, lng, timezone)
    times = calc.calculate_times(datetime.now())

    # Cache
    db.cache_prayer_times(today, city, times)
    return times


def get_next_prayer(lat: float, lng: float, timezone: str, city: str) -> Dict:
    """Get information about the next prayer."""
    times = get_prayer_times(lat, lng, timezone, city)
    now = datetime.now()
    current_time = now.hour * 60 + now.minute

    prayer_order = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
    prayer_names = {
        "fajr": "الفجر",
        "dhuhr": "الظهر",
        "asr": "العصر",
        "maghrib": "المغرب",
        "isha": "العشاء"
    }

    next_prayer = None
    min_diff = float('inf')

    for prayer in prayer_order:
        t = times.get(prayer, "00:00")
        try:
            h, m = map(int, t.split(":"))
            prayer_minutes = h * 60 + m
            diff = prayer_minutes - current_time
            if diff > 0 and diff < min_diff:
                min_diff = diff
                next_prayer = prayer
        except ValueError:
            continue

    # If no next prayer today, fajr is tomorrow
    if next_prayer is None:
        next_prayer = "fajr"
        t = times.get("fajr", "00:00")
        try:
            h, m = map(int, t.split(":"))
            min_diff = (h * 60 + m) + (24 * 60 - current_time)
        except ValueError:
            min_diff = 0

    hours_left = min_diff // 60
    minutes_left = min_diff % 60

    return {
        "name": prayer_names.get(next_prayer, next_prayer),
        "key": next_prayer,
        "time": times.get(next_prayer, "--:--"),
        "hours_left": hours_left,
        "minutes_left": minutes_left,
        "total_minutes": min_diff
    }


def format_prayer_times(times: Dict[str, str], city: str) -> str:
    """Format prayer times for display."""
    prayer_names = {
        "fajr": "🌅 الفجر",
        "sunrise": "🌄 الشروق",
        "dhuhr": "☀️ الظهر",
        "asr": "🌤 العصر",
        "maghrib": "🌇 المغرب",
        "isha": "🌙 العشاء",
        "midnight": "🌑 منتصف الليل"
    }

    result = f"🕌 <b>مواقيت الصلاة - {city}</b>\n"
    result += f"📅 {datetime.now().strftime('%Y-%m-%d')}\n\n"

    for key, name in prayer_names.items():
        time = times.get(key, "--:--")
        result += f"{name}: <code>{time}</code>\n"

    return result


def format_next_prayer(info: Dict) -> str:
    """Format next prayer info for display."""
    result = f"📍 <b>الصلاة القادمة: {info['name']}</b>\n\n"
    result += f"🕐 الوقت: <code>{info['time']}</code>\n"
    result += f"⏳ المتبقي: "

    if info['hours_left'] > 0:
        result += f"{info['hours_left']} ساعة "
    result += f"{info['minutes_left']} دقيقة"

    return result


def get_prayer_taqibat(prayer: str) -> Dict:
    """Get taqibat (supplications after prayer) for a specific prayer."""
    import json
    from pathlib import Path

    filepath = Path(__file__).parent.parent / "data" / "normalized" / "prayer_content" / f"{prayer}.json"
    if not filepath.exists():
        return {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def format_taqibat(data: Dict, prayer_name: str) -> str:
    """Format taqibat content for display."""
    TELEGRAM_LIMIT = 3900
    result = f"📿 <b>تعقيبات صلاة {prayer_name}</b>\n\n"

    # New format: data contains an "items" list
    if "items" in data:
        items = data["items"]
        if not items:
            result += "سيتم إضافة المحتوى قريباً إن شاء الله."
            return result
        for idx, item in enumerate(items):
            title = item.get("title", "")
            text = item.get("text", "")
            entry = ""
            if title:
                entry += f"✨ <b>{title}</b>\n"
            if text:
                display = text[:500] + "\n<i>...</i>" if len(text) > 500 else text
                entry += f"{display}\n\n"
            if len(result) + len(entry) > TELEGRAM_LIMIT:
                remaining = len(items) - idx
                result += f"\n<i>... و{remaining} تعقيبات أخرى</i>"
                break
            result += entry
        return result

    # Legacy format: keys like "tasbihat", "azkar", "duas", "taqibat" live directly in data
    has_content = False
    if data.get("tasbihat"):
        has_content = True
        result += "🟢 <b>التسبيحات:</b>\n"
        for item in data["tasbihat"]:
            result += f"  • {item}\n"
        result += "\n"

    if data.get("azkar"):
        has_content = True
        result += "📿 <b>الأذكار:</b>\n"
        for item in data["azkar"]:
            result += f"  • {item}\n"
        result += "\n"

    if data.get("duas"):
        has_content = True
        result += "🤲 <b>الأدعية:</b>\n"
        for item in data["duas"]:
            result += f"  • {item}\n"
        result += "\n"

    if data.get("taqibat"):
        has_content = True
        result += "✨ <b>التعقيبات:</b>\n"
        for item in data["taqibat"]:
            result += f"  • {item}\n"

    if not has_content:
        result += "سيتم إضافة المحتوى قريباً إن شاء الله."

    return result
