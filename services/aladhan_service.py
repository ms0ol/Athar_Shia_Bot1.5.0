"""
Athar Shia Bot - Aladhan API Service
بوت أثَر - خدمة API Aladhan للمواقيت

Uses Aladhan REST API (https://aladhan.com/prayer-times-api) as an external
source for accurate prayer times. Falls back to the local calculator if the
network is unavailable.

Calculation parameters:
    method  = 1   (Jafari / Ithna Ashari - المذهب الجعفري)
    school  = 1   (Hanafi - قاعدة الأصر 2× الظل)
    tune    = "0,0,0,0,0,0,0,0,0" (no manual offsets)
"""

import logging
from datetime import datetime
from typing import Dict, Optional
import aiohttp
import aiohttp.client_exceptions
import pytz  # مضاف لضمان استقرار حساب التاريخ الفعلي داخل العراق

logger = logging.getLogger(__name__)

ALADHAN_BASE = "https://api.aladhan.com/v1"
METHOD_JAFARI = 0
SCHOOL_HANAFI = 0

# تم إزالة الجلب التلقائي لـ Midnight من هنا لإجبار البوت على الحساب الجعفري اليدوي
_KEY_MAP = {
    "Fajr": "fajr",
    "Sunrise": "sunrise",
    "Dhuhr": "dhuhr",
    "Asr": "asr",
    "Sunset": "sunset",
    "Maghrib": "maghrib",
    "Isha": "isha",
}




async def fetch_aladhan_times(
    lat: float,
    lng: float,
    date: str = None,
    timeout: float = 8.0,
) -> Optional[Dict[str, str]]:
    """
    Fetch prayer times from Aladhan API for the given coordinates.

    Args:
        lat: Latitude (float)
        lng: Longitude (float)
        date: Date in DD-MM-YYYY format (default: today in Asia/Baghdad)
        timeout: Request timeout in seconds

    Returns:
        Dictionary with keys: fajr, sunrise, dhuhr, asr, sunset,
                              maghrib, isha, midnight
        or None if the API call fails.
    """
    # إصلاح ذكي: إذا كان السيرفر مستضافاً خارج العراق، datetime.now() قد تعطي تاريخاً خاطئاً ليلاً.
    # هنا نجبر النظام على جلب تاريخ اليوم الفعلي بحسب توقيت بغداد.
    if date is None:
        tz = pytz.timezone("Asia/Baghdad")
        date = datetime.now(tz).strftime("%d-%m-%Y")

    # داخل دالة fetch_aladhan_times قم بتحديث رابط الـ URL ليقبل معامل الـ tune والـ method الصحيح:
    url = (
        f"{ALADHAN_BASE}/timings/{date}"
        f"?latitude={lat}"
        f"&longitude={lng}"
        f"&method=0"  # استخدام 0 لمؤسسة لواء في قم لضبط المغرب
        f"&school={SCHOOL_HANAFI}"
        f"&tune=0,-10,0,0,0,0,0,0,0" # تقديم الفجر 10 دقائق لحل مشكلة التأخير
    )


    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"[Aladhan] HTTP {response.status} for {lat},{lng}")
                    return None

                data = await response.json()

                if data.get("code") != 200 or "data" not in data:
                    logger.warning(f"[Aladhan] API error: {data.get('status')}")
                    return None

                timings = data["data"]["timings"]
                result = {}

                # استخراج المواقيت وتنظيف النص المستلم (مثل قطع نصوص المناطق الزمنية المضافة كـ " (EEST)")
                for aladhan_key, our_key in _KEY_MAP.items():
                    time_str = timings.get(aladhan_key)
                    if time_str:
                        result[our_key] = time_str.split()[0][:5]

                # حساب منتصف الليل الشرعي (المذهب الجعفري): المنتصف الدقيق بين المغرب وفجر اليوم التالي
                if "maghrib" in result and "fajr" in result:
                    try:
                        h_maghrib, m_maghrib = map(int, result["maghrib"].split(":"))
                        maghrib_mins = h_maghrib * 60 + m_maghrib

                        h_fajr, m_fajr = map(int, result["fajr"].split(":"))
                        fajr_mins = h_fajr * 60 + m_fajr

                        # تحويل وقت الفجر إلى دقائق مضافة لليوم التالي (+24 ساعة) لضمان دقة عملية الطرح
                        fajr_next_mins = fajr_mins + 24 * 60
                        midnight_mins = (maghrib_mins + fajr_next_mins) / 2
                        midnight_mins %= (24 * 60)

                        result["midnight"] = f"{int(midnight_mins // 60):02d}:{int(midnight_mins % 60):02d}"
                    except Exception as calc_err:
                        logger.error(f"[Aladhan] Midnight manual calculation failed: {calc_err}")
                        result["midnight"] = "23:59"  # قيمة احتياطية آمنة في حال حدوث خطأ غير متوقع في التحليل

                logger.info(f"[Aladhan] ✅ Timings successfully fetched for {lat},{lng}. Midnight: {result.get('midnight')}")
                return result

    except (aiohttp.ClientError, aiohttp.client_exceptions.ClientConnectorError) as e:
        logger.warning(f"[Aladhan] Network error: {e}")
        return None
    except Exception as e:
        logger.error(f"[Aladhan] Unexpected error: {e}")
        return None


