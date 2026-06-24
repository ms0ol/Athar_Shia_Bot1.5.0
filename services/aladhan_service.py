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

logger = logging.getLogger(__name__)

ALADHAN_BASE = "https://api.aladhan.com/v1"

# Jafari/Shia method identifiers
METHOD_JAFARI = 1
SCHOOL_HANAFI = 1

# Mapping from Aladhan keys to our internal keys
_KEY_MAP = {
    "Fajr": "fajr",
    "Sunrise": "sunrise",
    "Dhuhr": "dhuhr",
    "Asr": "asr",
    "Sunset": "sunset",
    "Maghrib": "maghrib",
    "Isha": "isha",
    "Midnight": "midnight",
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
        date: Date in DD-MM-YYYY format (default: today)
        timeout: Request timeout in seconds

    Returns:
        Dictionary with keys: fajr, sunrise, dhuhr, asr, sunset,
                              maghrib, isha, midnight
        or None if the API call fails.
    """
    if date is None:
        date = datetime.now().strftime("%d-%m-%Y")

    url = (
        f"{ALADHAN_BASE}/timings/{date}"
        f"?latitude={lat}"
        f"&longitude={lng}"
        f"&method={METHOD_JAFARI}"
        f"&school={SCHOOL_HANAFI}"
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
                for aladhan_key, our_key in _KEY_MAP.items():
                    time_str = timings.get(aladhan_key)
                    if time_str:
                        result[our_key] = time_str

                # If Aladhan didn't return midnight, compute it locally
                if "midnight" not in result and "maghrib" in result and "fajr" in result:
                    try:
                        h, m = map(int, result["maghrib"].split(":"))
                        maghrib_mins = h * 60 + m
                        h, m = map(int, result["fajr"].split(":"))
                        fajr_mins = h * 60 + m
                        # Midnight = halfway between Maghrib and Fajr+24h
                        midnight_mins = (maghrib_mins + fajr_mins + 24 * 60) / 2
                        midnight_mins %= (24 * 60)
                        result["midnight"] = f"{int(midnight_mins // 60):02d}:{int(midnight_mins % 60):02d}"
                    except Exception:
                        pass

                logger.info(f"[Aladhan] ✅ Timings fetched for {lat},{lng}: {result.get('fajr')} - {result.get('isha')}")
                return result

    except (aiohttp.ClientError, aiohttp.client_exceptions.ClientConnectorError) as e:
        logger.warning(f"[Aladhan] Network error: {e}")
        return None
    except Exception as e:
        logger.error(f"[Aladhan] Unexpected error: {e}")
        return None
