"""
Athar Shia Bot - Database Manager
بوت آثار الشيعة - إدارة قاعدة البيانات
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path(__file__).parent / "storage" / "bot.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Initialize all database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # ─── Users Table ───
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            city TEXT DEFAULT 'بغداد',
            timezone TEXT DEFAULT 'Asia/Baghdad',
            latitude REAL DEFAULT 33.3152,
            longitude REAL DEFAULT 44.3661,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ─── Subscriptions Table ───
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)

    # ─── Sent Content Table ───
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sent_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content_type TEXT NOT NULL,
            content_id TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)

    # ─── Bot State Table ───
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_state (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ─── Prayer Times Cache ───
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prayer_times_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            city TEXT NOT NULL,
            fajr TEXT,
            sunrise TEXT,
            dhuhr TEXT,
            asr TEXT,
            maghrib TEXT,
            isha TEXT,
            midnight TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ─── User Operations ───

def add_user(user_id: int, username: Optional[str], full_name: Optional[str]) -> bool:
    """Add a new user or update existing one."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name,
                last_active = CURRENT_TIMESTAMP
        """, (user_id, username, full_name))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user data by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users() -> List[Dict[str, Any]]:
    """Get all users for broadcast."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_user_location(user_id: int, city: str, lat: float, lng: float) -> bool:
    """Update user's location settings."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE users SET city = ?, latitude = ?, longitude = ?
            WHERE user_id = ?
        """, (city, lat, lng, user_id))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error:
        return False
    finally:
        conn.close()


# ─── Subscription Operations ───

def toggle_subscription(user_id: int, sub_type: str) -> bool:
    """Toggle a subscription on/off. Returns new state."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT is_active FROM subscriptions
        WHERE user_id = ? AND type = ?
    """, (user_id, sub_type))
    row = cursor.fetchone()

    if row:
        new_state = 0 if row["is_active"] else 1
        cursor.execute("""
            UPDATE subscriptions SET is_active = ?
            WHERE user_id = ? AND type = ?
        """, (new_state, user_id, sub_type))
    else:
        new_state = 1
        cursor.execute("""
            INSERT INTO subscriptions (user_id, type, is_active)
            VALUES (?, ?, 1)
        """, (user_id, sub_type))

    conn.commit()
    conn.close()
    return bool(new_state)


def get_user_subscriptions(user_id: int) -> Dict[str, bool]:
    """Get all subscriptions for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT type, is_active FROM subscriptions WHERE user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return {row["type"]: bool(row["is_active"]) for row in rows}


def get_subscribed_users(sub_type: str) -> List[Dict[str, Any]]:
    """Get all users subscribed to a specific type."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.* FROM users u
        JOIN subscriptions s ON u.user_id = s.user_id
        WHERE s.type = ? AND s.is_active = 1
    """, (sub_type,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ─── Content Tracking ───

def is_content_sent(user_id: int, content_type: str, content_id: str) -> bool:
    """Check if content was already sent to user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM sent_content
        WHERE user_id = ? AND content_type = ? AND content_id = ?
    """, (user_id, content_type, content_id))
    row = cursor.fetchone()
    conn.close()
    return row is not None


def mark_content_sent(user_id: int, content_type: str, content_id: str):
    """Mark content as sent to user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sent_content (user_id, content_type, content_id)
        VALUES (?, ?, ?)
    """, (user_id, content_type, content_id))
    conn.commit()
    conn.close()


def get_sent_content_ids(user_id: int, content_type: str) -> List[str]:
    """Get all sent content IDs for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT content_id FROM sent_content
        WHERE user_id = ? AND content_type = ?
    """, (user_id, content_type))
    rows = cursor.fetchall()
    conn.close()
    return [row["content_id"] for row in rows]


def reset_daily_tracking():
    """Reset daily sent content tracking (run at midnight)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sent_content")
    conn.commit()
    conn.close()


# ─── Bot State ───

def get_state(key: str, default: str = "") -> str:
    """Get a bot state value."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM bot_state WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default


def set_state(key: str, value: str):
    """Set a bot state value."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bot_state (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = CURRENT_TIMESTAMP
    """, (key, value))
    conn.commit()
    conn.close()


# ─── Prayer Times Cache ───

def cache_prayer_times(date: str, city: str, times: Dict[str, str]):
    """Cache prayer times for a date."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO prayer_times_cache
        (date, city, fajr, sunrise, dhuhr, asr, maghrib, isha, midnight)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        date, city,
        times.get("fajr", ""),
        times.get("sunrise", ""),
        times.get("dhuhr", ""),
        times.get("asr", ""),
        times.get("maghrib", ""),
        times.get("isha", ""),
        times.get("midnight", "")
    ))
    conn.commit()
    conn.close()


def get_cached_prayer_times(date: str, city: str) -> Optional[Dict[str, str]]:
    """Get cached prayer times for a date."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM prayer_times_cache WHERE date = ? AND city = ?
    """, (date, city))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "fajr": row["fajr"],
            "sunrise": row["sunrise"],
            "dhuhr": row["dhuhr"],
            "asr": row["asr"],
            "maghrib": row["maghrib"],
            "isha": row["isha"],
            "midnight": row["midnight"]
        }
    return None
