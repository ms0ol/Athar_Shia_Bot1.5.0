"""
Migrate hijri_calendar.json → data/normalized/event_content/events.json
Flat structure: one item per day that has events.
hijri_date format: "DD-MM"
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC  = ROOT / "hijri_calendar.json"
DST  = ROOT / "data" / "normalized" / "event_content" / "events.json"

MONTH_NUMBERS = {
    "محرم الحرام":       1,
    "صفر الأحزان":       2,
    "ربیع‌ الاول":        3,
    "ربیع‌ الثاني":       4,
    "جمادي الاولی":      5,
    "جمادي الثانیة":     6,
    "رجب المرجب":        7,
    "شعبان المعظم":      8,
    "رمضان المبارک":     9,
    "شوال المکرم":       10,
    "ذي القعدة الحرام":  11,
    "ذي الحجة الحرام":   12,
}

MONTH_NAMES_AR = {
    1:  "محرم الحرام",
    2:  "صفر الأحزان",
    3:  "ربيع الأول",
    4:  "ربيع الثاني",
    5:  "جمادى الأولى",
    6:  "جمادى الآخرة",
    7:  "رجب المرجب",
    8:  "شعبان المعظم",
    9:  "رمضان المبارك",
    10: "شوال المكرم",
    11: "ذو القعدة",
    12: "ذو الحجة",
}


def migrate():
    with open(SRC, encoding="utf-8") as f:
        calendar = json.load(f)

    items = []
    counter = 1
    errors = []

    for month_obj in calendar:
        month_name = month_obj.get("month", "").strip()
        month_num  = MONTH_NUMBERS.get(month_name)

        if month_num is None:
            errors.append(f"Unknown month name: '{month_name}'")
            continue

        for day_obj in month_obj.get("days", []):
            day_str  = str(day_obj.get("day", "")).strip()
            text_val = day_obj.get("text", "").strip()

            if not day_str or not text_val:
                errors.append(f"Skipping empty day in month {month_name}")
                continue

            try:
                day_int = int(day_str)
            except ValueError:
                errors.append(f"Non-integer day '{day_str}' in month {month_name}")
                continue

            hijri_date = f"{day_int:02d}-{month_num:02d}"

            items.append({
                "id":          f"EV{counter:04d}",
                "hijri_date":  hijri_date,
                "month":       MONTH_NAMES_AR.get(month_num, month_name),
                "day":         day_str,
                "text":        text_val,
            })
            counter += 1

    output = {
        "metadata": {
            "total":       len(items),
            "source":      "hijri_calendar.json",
            "format":      "DD-MM",
            "description": "مناسبات التقويم الهجري مستخرجة تلقائياً من hijri_calendar.json",
        },
        "items": items,
    }

    DST.parent.mkdir(parents=True, exist_ok=True)
    with open(DST, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return len(items), errors


if __name__ == "__main__":
    count, errs = migrate()
    print(f"✅ تم إنشاء {count} عنصراً في events.json")
    if errs:
        print(f"⚠️  {len(errs)} تحذير:")
        for e in errs:
            print(f"   - {e}")
    else:
        print("✅ لا توجد أخطاء")
