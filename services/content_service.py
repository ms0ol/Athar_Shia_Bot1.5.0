"""
Athar Shia Bot - Content Service
بوت آثار الشيعة - خدمة المحتوى
"""

import json
import random
from pathlib import Path
from typing import Optional, Dict, Any, List

import database as db

DATA_DIR = Path(__file__).parent.parent / "data" / "normalized"


def load_json(filepath: Path) -> Dict:
    """Load and return JSON file contents."""
    if not filepath.exists():
        return {"items": []}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"items": []}


def get_random_item(content_type: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Get a random content item that hasn't been sent to the user.
    content_type: hadith, wisdom_short, wisdom_deep, wisdom_featured,
                  daily_dua, munajat, ziyarat
    """
    filepath = DATA_DIR / "daily_content" / f"{content_type}.json"
    data = load_json(filepath)
    items = data.get("items", [])

    if not items:
        return None

    # Filter out already sent content if user_id provided
    if user_id is not None:
        sent_ids = db.get_sent_content_ids(user_id, content_type)
        available = [item for item in items if item.get("id") not in sent_ids]
        if available:
            items = available
        else:
            # All sent, reset tracking for this type
            items = data.get("items", [])

    return random.choice(items)


def get_daily_content(user_id: int) -> Dict[str, Any]:
    """Get all daily content for a user (with deduplication)."""
    result = {}

    hadith = get_random_item("hadith", user_id)
    if hadith:
        result["hadith"] = hadith
        db.mark_content_sent(user_id, "hadith", hadith["id"])

    wisdom = get_random_item("wisdom_featured", user_id)
    if not wisdom:
        wisdom = get_random_item("wisdom_short", user_id)
    if wisdom:
        result["wisdom"] = wisdom
        db.mark_content_sent(user_id, "wisdom", wisdom["id"])

    dua = get_random_item("daily_dua", user_id)
    if dua:
        result["dua"] = dua
        db.mark_content_sent(user_id, "daily_dua", dua["id"])

    munajat = get_random_item("munajat", user_id)
    if munajat:
        result["munajat"] = munajat
        db.mark_content_sent(user_id, "munajat", munajat["id"])

    return result


def get_content_by_id(content_type: str, content_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific content item by ID."""
    filepath = DATA_DIR / "daily_content" / f"{content_type}.json"
    data = load_json(filepath)
    for item in data.get("items", []):
        if item.get("id") == content_id:
            return item
    return None


def get_all_items(content_type: str) -> List[Dict[str, Any]]:
    """Get all items of a content type."""
    filepath = DATA_DIR / "daily_content" / f"{content_type}.json"
    data = load_json(filepath)
    return data.get("items", [])


def format_hadith(item: Dict) -> str:
    """Format a hadith item for display."""
    text = item.get("text", "")
    source = item.get("source", "")
    imam = item.get("imam", "")

    result = f"📖 <b>حديث شريف</b>\n\n"
    if imam:
        result += f"👤 <b>عن الإمام {imam} عليه السلام:</b>\n\n"
    result += f"❝ {text} ❞\n\n"
    if source:
        result += f"📚 <i>{source}</i>"
    return result


def format_wisdom(item: Dict) -> str:
    """Format a wisdom item for display."""
    text = item.get("text", "")
    source = item.get("source", "")
    imam = item.get("imam", "")

    result = f"💎 <b>حكمة</b>\n\n"
    if imam:
        result += f"👤 <b>الإمام {imam} عليه السلام</b>\n\n"
    result += f"❝ {text} ❞\n\n"
    if source:
        result += f"📚 <i>{source}</i>"
    return result


def format_dua(item: Dict) -> str:
    """Format a dua item for display."""
    text = item.get("text", "")
    title = item.get("title", "")
    source = item.get("source", "")

    result = f"🤲 <b>{title or 'دعاء'}</b>\n\n"
    result += f"{text}\n\n"
    if source:
        result += f"📚 <i>{source}</i>"
    return result


def format_munajat(item: Dict) -> str:
    """Format a munajat item for display."""
    text = item.get("text", "")
    title = item.get("title", "")
    number = item.get("number", "")

    result = f"✨ <b>مناجاة {number or ''}</b>\n"
    if title:
        result += f"📌 {title}\n"
    result += f"\n{text}\n\n"
    result += "— صاحب الزمان الإمام المهدي عليه السلام"
    return result


def format_ziyarat(item: Dict) -> str:
    """Format a ziyarat item for display."""
    text = item.get("text", "")
    title = item.get("title", "")
    imam = item.get("imam", "")

    result = f"🕌 <b>{title or 'زيارة'}</b>\n"
    if imam:
        result += f"👤 {imam} عليه السلام\n"
    result += f"\n{text}"
    return result


def get_random_content_for_subscription(sub_type: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Get content for daily subscription."""
    content_map = {
        "hadith_daily": ("hadith", format_hadith),
        "wisdom_daily": ("wisdom_short", format_wisdom),
        "dua_daily": ("daily_dua", format_dua),
        "munajat_daily": ("munajat", format_munajat),
    }

    if sub_type not in content_map:
        return None

    content_type, formatter = content_map[sub_type]
    item = get_random_item(content_type, user_id)
    if item:
        db.mark_content_sent(user_id, content_type, item["id"])
        return {
            "item": item,
            "text": formatter(item),
            "type": content_type
        }
    return None
