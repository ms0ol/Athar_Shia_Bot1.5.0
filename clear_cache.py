import sqlite3
from pathlib import Path

# هكذا المسار سيكون صحيحاً لأنه ينطلق من المجلد الرئيسي للمشروع
DB_PATH = Path(__file__).parent / "storage" / "bot.db"

try:
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM prayer_times_cache")
    conn.commit()
    conn.close()
    print("🗑️ تم تنظيف كاش المواقيت بنجاح من المسار الصحيح!")
except Exception as e:
    print(f"❌ فشل التنظيف: {e}")
