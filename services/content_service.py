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

# ─── Content Type → File Path Routing ───
# Maps content_type → (subfolder, filename)
_CONTENT_ROUTES = {
    "hadith":           ("daily_content", "hadith"),
    "wisdom":           ("daily_content", "wisdom"),
    "wisdom_short":     ("daily_content", "wisdom"),
    "wisdom_featured":  ("daily_content", "wisdom"),
    "wisdom_deep":      ("daily_content", "wisdom"),
    "daily_dua":        ("daily_content", "daily_dua"),
    "munajat":          ("library",       "munajat"),
    "ziyarat":          ("library",       "ziyarat"),
}

# Wisdom type filter mapping
_WISDOM_TYPE_FILTER = {
    "wisdom_short":    "short",
    "wisdom_featured": "featured",
    "wisdom_deep":     "deep",
}


def load_json(filepath: Path) -> Dict:
    """Load and return JSON file contents."""
    if not filepath.exists():
        return {"items": []}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"items": []}


def _resolve_path(content_type: str) -> Path:
    """Resolve the file path for a given content type."""
    if content_type in _CONTENT_ROUTES:
        subfolder, filename = _CONTENT_ROUTES[content_type]
        return DATA_DIR / subfolder / f"{filename}.json"
    return DATA_DIR / "daily_content" / f"{content_type}.json"


def _get_items(content_type: str) -> List[Dict[str, Any]]:
    """Load items for content_type, applying type filter for wisdom variants."""
    filepath = _resolve_path(content_type)
    data = load_json(filepath)
    items = data.get("items", [])

    wisdom_type = _WISDOM_TYPE_FILTER.get(content_type)
    if wisdom_type:
        items = [i for i in items if i.get("type") == wisdom_type]

    return items


def get_random_item(content_type: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Get a random content item that hasn't been sent to the user.
    content_type: hadith, wisdom, wisdom_short, wisdom_featured, wisdom_deep,
                  daily_dua, munajat, ziyarat
    """
    items = _get_items(content_type)

    if not items:
        return None

    if user_id is not None:
        sent_ids = db.get_sent_content_ids(user_id, content_type)
        available = [item for item in items if item.get("id") not in sent_ids]
        if available:
            items = available

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
        wisdom = get_random_item("wisdom", user_id)
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
    items = _get_items(content_type)
    for item in items:
        if item.get("id") == content_id:
            return item
    return None


def get_all_items(content_type: str) -> List[Dict[str, Any]]:
    """Get all items of a content type."""
    return _get_items(content_type)


def format_hadith(item: Dict) -> str:
    """Format a hadith item for display."""
    text = item.get("text", "")
    source = item.get("source", "")
    author = item.get("author", item.get("imam", ""))

    result = f"📖 <b>حديث شريف</b>\n\n"
    if author:
        result += f"👤 <b>{author}</b>\n\n"
    result += f"❝ {text} ❞\n\n"
    if source:
        result += f"📚 <i>{source}</i>"
    return result


def format_wisdom(item: Dict) -> str:
    """Format a wisdom item for display."""
    text = item.get("text", "")
    source = item.get("source", "")
    author = item.get("author", item.get("imam", ""))

    result = f"💎 <b>حكمة</b>\n\n"
    if author:
        result += f"👤 <b>{author}</b>\n\n"
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
    if text:
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
    result += f"\n{text[:3000]}"
    if len(text) > 3000:
        result += "\n\n<i>... (يتبع)</i>"
    return result


def format_ziyarat(item: Dict) -> str:
    """Format a ziyarat item for display."""
    text = item.get("text", "")
    title = item.get("title", "")
    author = item.get("author", item.get("imam", ""))

    result = f"🕌 <b>{title or 'زيارة'}</b>\n"
    if author:
        result += f"👤 {author} عليه السلام\n"
    result += f"\n{text[:3000]}"
    if len(text) > 3000:
        result += "\n\n<i>... (يتبع)</i>"
    return result


def get_random_content_for_subscription(sub_type: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Get content for daily subscription."""
    content_map = {
        "hadith_daily":  ("hadith",    format_hadith),
        "wisdom_daily":  ("wisdom",    format_wisdom),
        "dua_daily":     ("daily_dua", format_dua),
        "munajat_daily": ("munajat",   format_munajat),
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
