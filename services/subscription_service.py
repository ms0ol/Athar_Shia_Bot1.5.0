"""
Athar Shia Bot - Subscription Service
بوت آثار الشيعة - خدمة الاشتراكات
"""

from typing import Dict, List
import database as db


# ─── Subscription Types ───

SUBSCRIPTION_TYPES = {
    "hadith_daily": {
        "name": "حديث يومي",
        "emoji": "📖",
        "description": "يومي - حديث من أهل البيت عليهم السلام"
    },
    "wisdom_daily": {
        "name": "حكمة يومية",
        "emoji": "💎",
        "description": "يومي - حكمة من المعصومين"
    },
    "dua_daily": {
        "name": "دعاء يومي",
        "emoji": "🤲",
        "description": "يومي - دعاء مختار"
    },
    "munajat_daily": {
        "name": "مناجاة يومية",
        "emoji": "✨",
        "description": "يومي - مناجاة من المناجاة الخمسة عشر"
    },
    "prayer_reminder": {
        "name": "تذكير الصلاة",
        "emoji": "🕌",
        "description": "عند كل صلاة - تذكير بوقت الصلاة"
    },
    "event_reminder": {
        "name": "تذكير المناسبات",
        "emoji": "📅",
        "description": "عند وجود مناسبة - إشعار بالمناسبة وأعمالها"
    },
}


def get_subscription_list(user_id: int) -> List[Dict]:
    """Get all subscriptions with their current state for a user."""
    user_subs = db.get_user_subscriptions(user_id)
    result = []

    for key, info in SUBSCRIPTION_TYPES.items():
        is_active = user_subs.get(key, False)
        result.append({
            "key": key,
            "name": info["name"],
            "emoji": info["emoji"],
            "description": info["description"],
            "is_active": is_active
        })

    return result


def toggle_subscription(user_id: int, sub_key: str) -> bool:
    """Toggle a subscription. Returns new state."""
    return db.toggle_subscription(user_id, sub_key)


def format_subscriptions_list(subs: List[Dict]) -> str:
    """Format subscriptions list for display."""
    result = "🔔 <b>اشتراكاتي</b>\n\n"
    result += "اضغط على الزر لتفعيل/إلغاء:\n\n"

    for sub in subs:
        status = "✅" if sub["is_active"] else "❌"
        result += f"{sub['emoji']} {sub['name']} - {status}\n"
        result += f"   <i>{sub['description']}</i>\n\n"

    return result


def get_active_subscribers(sub_type: str) -> List[Dict]:
    """Get all users subscribed to a specific type."""
    return db.get_subscribed_users(sub_type)
