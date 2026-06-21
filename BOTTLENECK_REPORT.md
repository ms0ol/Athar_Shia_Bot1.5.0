# Athar Shia Bot - Performance Bottleneck Audit

> **Date:** 2026-06-21
> **Scope:** All Python files
> **Task:** Identify and document performance issues without fixing them

---

## Severity Scale

| Level | Impact | Description |
|-------|--------|-------------|
| 5 | Critical | Will cause hangs or crashes at scale |
| 4 | High | Will cause severe lag or timeouts |
| 3 | Medium | Will cause noticeable slowdowns |
| 2 | Low | Inefficient but manageable |
| 1 | Minor | Cosmetic / edge case |

---

## Level 5 - Critical

### 1. No Rate Limiting on Broadcast Loops

**Files & Lines:**
- `scheduler.py:61-129` — `_prayer_reminder_loop()`
- `scheduler.py:148-162` — `_daily_content_loop()`
- `scheduler.py:177-209` — `_event_check_loop()`
- `scheduler.py:235-273` — `_tasbih_reminder_loop()`
- `scheduler.py:278-326` — `_pre_prayer_reminder_loop()`
- `scheduler.py:434-448` — `send_broadcast()`

**Problem:**
All broadcast loops iterate through every subscribed user and send messages sequentially without any `asyncio.sleep()` between API calls. Telegram Bot API has rate limits (approx 30 messages/second to different users, 1 msg/sec to the same user). With hundreds or thousands of users, these loops will:
- Hit rate limits and receive 429 errors
- Block the event loop for extended periods
- Cause subsequent user interactions to hang or timeout

**Example from `_prayer_reminder_loop`:**
```python
users = db.get_subscribed_users("prayer_reminder")
for user in users:
    # ... prayer time calculation per user ...
    await self.bot.send_message(user["user_id"], text, parse_mode="HTML")
    # No sleep, no batching, no concurrency control
```

**Impact:** The bot will become unresponsive during broadcast windows (5 AM, prayer times, 9 PM). Each message is a blocking HTTP request. With 1000 users, a single loop could take 30+ seconds of wall-clock time.

---

## Level 4 - High

### 2. No Connection Pool for SQLite

**File:** `database.py:15-21`

```python
def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
```

**Problem:** Every single database call opens a new `sqlite3.connect()` and closes it implicitly. This creates significant overhead:
- File descriptor open/close on every query
- WAL mode overhead (if enabled) without connection reuse
- No transaction batching possible across multiple calls

**Impact:** Under concurrent user load, the bot will spend more time opening/closing DB connections than executing queries. This is especially bad for the scheduler loops which query the DB repeatedly inside tight loops.

---

### 3. JSON Files Loaded from Disk on Every Request

**File:** `services/content_service.py:41-70`

```python
def load_json(filepath: Path) -> Dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def _get_items(content_type: str) -> List[Dict[str, Any]]:
    data = load_json(filepath)
    items = data.get("items", [])
    # ...
    return items
```

**Problem:** `_get_items()` is called for every content request (daily content, random hadith, etc.) and performs a full `json.load()` from disk. The content files are static — they never change at runtime. There is no in-memory cache.

**Impact:** Each `/daily` command triggers disk I/O + JSON parsing. Under load, this adds 10-50ms per request unnecessarily. With 1000 users, this is a measurable CPU and I/O drain.

---

### 4. Prayer Times Recalculated Per User Instead of Per Location

**File:** `services/prayer_service.py` (inferred from usage in `scheduler.py`)

**Problem:** In `_prayer_reminder_loop`, the code calls `get_prayer_times()` inside the user loop:

```python
for user in users:
    times = get_prayer_times(
        user.get("latitude", config.LATITUDE),
        user.get("longitude", config.LONGITUDE),
        user.get("timezone", config.TIMEZONE),
        user.get("city", config.CITY)
    )
```

**Impact:** If 500 users are in Baghdad, the prayer times are calculated 500 times. The calculation is CPU-intensive (trigonometric calculations). This should be cached by `(lat, lon, date)` tuple.

---

## Level 3 - Medium

### 5. All Scheduler Loops Wake Every 55-60 Seconds

**Files:**
- `scheduler.py:61-129` — sleep 55s
- `scheduler.py:148-162` — sleep 55s
- `scheduler.py:177-209` — sleep 55s
- `scheduler.py:235-273` — sleep 55s
- `scheduler.py:278-326` — sleep 55s
- `scheduler.py:330-335` — sleep 55s
- `scheduler.py:374-380` — sleep 55s

**Problem:** 8 separate `while` loops each wake up every 55-60 seconds to check the time. Even when nothing needs to be sent, they:
- Query the database
- Compare time strings
- Go back to sleep

**Impact:** Wasted CPU cycles and DB connections. The loops could be consolidated into a single event-driven scheduler or use `asyncio` event scheduling (e.g., `loop.call_at()`).

---

### 6. Admin Notification Loop Sends to All Admins Without Error Handling

**File:** `handlers.py:89-104`

```python
for admin_id in config.ADMIN_IDS:
    try:
        await message.bot.send_message(admin_id, notif_text, parse_mode="HTML")
    except Exception:
        pass
```

**Problem:** While not a broadcast-to-users issue, this pattern (fire-and-forget with bare `except`) silently swallows all errors including rate limits, network failures, and invalid chat IDs.

**Impact:** Hard to diagnose delivery failures. If admins are unreachable, the bot silently fails.

---

### 7. No Pagination on `get_all_users()` or `get_subscribed_users()`

**File:** `database.py` (inferred from `scheduler.py` usage)

**Problem:** `db.get_all_users()` and `db.get_subscribed_users()` return the entire user list into memory as a single list. There is no pagination or cursor-based iteration.

**Impact:** As the user base grows, these queries will load increasingly large result sets into RAM. Combined with the sequential broadcast loops, this creates a memory + time + rate-limit triple bottleneck.

---

## Level 2 - Low

### 8. `get_random_item()` Loads Full Content List Every Time

**File:** `services/content_service.py:73-93`

**Problem:** `get_random_item()` calls `_get_items()` which loads the entire JSON file, then filters it, then picks one random item. This means the entire content catalog is loaded into memory for every single user request.

**Impact:** Wasted memory and CPU. If a content file has 10,000 items, every request loads all 10,000 into RAM.

---

## Summary Table

| # | Issue | Severity | File(s) | Line(s) |
|---|-------|----------|---------|---------|
| 1 | No rate limiting on broadcast loops | 5 | `scheduler.py` | 61-129, 148-162, 177-209, 235-273, 278-326, 434-448 |
| 2 | No SQLite connection pool | 4 | `database.py` | 15-21 |
| 3 | JSON loaded from disk on every request | 4 | `services/content_service.py` | 41-70 |
| 4 | Prayer times recalculated per user | 4 | `scheduler.py` | ~68-72 (inside loop) |
| 5 | 8 busy-waiting scheduler loops | 3 | `scheduler.py` | Multiple |
| 6 | Bare exception in admin notification | 3 | `handlers.py` | 89-104 |
| 7 | No pagination on user queries | 3 | `database.py` | Inferred |
| 8 | Full content catalog loaded per request | 2 | `services/content_service.py` | 73-93 |

---

*Report generated without code changes. All findings are documented for future optimization work.*
