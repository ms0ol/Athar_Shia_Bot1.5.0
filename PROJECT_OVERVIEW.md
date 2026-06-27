# 📋 توثيق مشروع أثَر | ATHAR — نظرة شاملة

---

## 🏗️ طريقة عمل البوت (Architecture)

```
المستخدم على تيليغرام
        ↓
   app.py  ← نقطة الدخول الرئيسية
        ↓
   Dispatcher (aiogram)
        ↓
   RateLimitMiddleware  ← فلترة الطلبات المتكررة
        ↓
   handlers/    ← مجلد معالجات مُقسَّم (aiogram v3)
        ↓
┌─────────────────────────────────────┐
│           Services Layer            │
│  prayer_service  |  content_service │
│  event_service   |  nav_service     │
│  subscription_service               │
└─────────────────────────────────────┘
        ↓
   database.py  ← SQLite (storage/bot.db)
        ↓
   data/normalized/*.json  ← محتوى ثابت

   scheduler.py  ← مهام مجدولة (مستقلة)
        ↓
   aladhan_service.py  ← API خارجي لمواقيت الصلاة
```

---

## 📁 ملفات الكود (Python)

### `app.py` — 143 سطر ✅ (مُحدَّث لـ aiogram v3)
**الدور:** نقطة الدخول الرئيسية — تشغيل البوت

| ما يفعله | التفاصيل |
|---|---|
| يُنشئ Bot و Dispatcher | مع DefaultBotProperties (parse_mode HTML) |
| يسجّل الـ Router | من handlers/__init__.py (main_router) |
| يشغّل Middleware | RateLimitMiddleware على message و callback |
| on_startup | يهيّئ DB، يشغّل الـ Scheduler، يضبط أوامر البوت |
| on_shutdown | يوقف الـ Scheduler، يغلق الجلسة |
| PID Lock | يمنع تشغيل نسختين في آنٍ واحد |

**ما ينقص:** لا شيء — الملف مكتمل بعد التحديث.

---

### `handlers/` — مجلد المعالجات ✅ (aiogram v3)
**الدور:** معالجة جميع أوامر التيليغرام والأزرار (Callbacks)

| الملف | القسم | الأوامر / Callbacks | السطور |
|---|---|---|---|
| `handlers/common.py` | أوامر عامة وقوائم | `/start`, `/menu`, `/about`, `/id`, `menu:*` | 310 |
| `handlers/ibadat.py` | العبادات والتعقيبات والمكتبة | `ibadat:*`, `taqibat:*`, `library:*`, `dua:random`... | 415 |
| `handlers/prayer.py` | الصلاة والموقع | `/prayer`, `/city`, `prayer:*`, `location:*`, GPS | 298 |
| `handlers/events.py` | المناسبات والتقويم الهجري | `/event`, `event:*` | 68 |
| `handlers/daily.py` | المحتوى اليومي والمفضلة والاشتراكات | `/daily`, `/subs`, `daily:*`, `sub_toggle:*`, `fav:*`, `*_lib:*` | 365 |
| `handlers/admin.py` | أوامر الأدمن والبث | `/admin`, `/stats`, `/broadcast`, `/errors` | 183 |
| `handlers/__init__.py` | تجميع وربط الـ Routers | يستير ويدمج كلـ Routers | 25 |

**التحديثات المطبَّقة (v2 → v3):**
- `Dispatcher` → `Router` مع Decorators (`@router.message(Command(...))`)
- `message.get_args()` → `CommandObject` كـ parameter
- `aiogram.utils.exceptions` → `aiogram.exceptions` (`TelegramBadRequest`)
- `register_message_handler` / `register_callback_query_handler` → Decorators على Router
- `ReplyKeyboardMarkup().add()` → `ReplyKeyboardMarkup(keyboard=[[...]])`
- `InlineKeyboardMarkup().add()/.row()` → `InlineKeyboardMarkup(inline_keyboard=[[...]])`

---

### `config.py` — 89 سطر ✅
**الدور:** إعدادات البوت من متغيرات البيئة

| المتغير | القيمة الافتراضية | المصدر |
|---|---|---|
| `BOT_TOKEN` | — | Secret في Replit |
| `ADMIN_IDS` | `[8055247329]` | env var (shared) |
| `CHANNEL_ID` | `@your_channel` | env var |
| `TIMEZONE` | `Asia/Baghdad` | env var |
| `CITY` | `بغداد` | env var |
| `LATITUDE` | `33.3152` | env var |
| `LONGITUDE` | `44.3661` | env var |
| `PRAYER_METHOD` | `1` (جعفري) | env var |
| `MAX_DAILY_CONTENT` | `3` | env var |
| `ENABLE_SUBSCRIPTIONS` | `true` | env var |
| `HIJRI_OFFSET` | `-1` | env var |
| `NEW_USER_NOTIFICATIONS` | `true` | env var |

**ما ينقص:** لا شيء.

---

### `database.py` — 569 سطر ✅
**الدور:** طبقة البيانات — SQLite محلي في `storage/bot.db`

**الجداول:**

| الجدول | الحقول | الدور |
|---|---|---|
| `users` | user_id, username, full_name, city, timezone, latitude, longitude, created_at, last_active | بيانات المستخدمين |
| `subscriptions` | user_id, type, is_active | اشتراكات الإشعارات |
| `sent_content` | user_id, content_type, content_id | تتبع المحتوى المُرسَل |
| `bot_state` | key, value | حالة البوت (مفاتيح/قيم) |
| `prayer_times_cache` | date, city, fajr..isha | كاش أوقات الصلاة |
| `dua_files` | dua_id, file_id, title | file_id للـ PDFs المسجّلة |
| `favorites` | user_id, content_type, content_id, title | مفضلات المستخدم |
| `error_logs` | user_id, command, error_msg | سجل الأخطاء |

**ما ينقص:** لا شيء — المكتبة مكتملة.

---

### `scheduler.py` — 481 سطر ✅
**الدور:** مهام مجدولة تعمل في الخلفية باستخدام `asyncio`

| المهمة | التوقيت | الوصف |
|---|---|---|
| `_prayer_reminder_loop` | كل دقيقة | إشعار عند دخول وقت الصلاة |
| `_pre_prayer_reminder_loop` | كل دقيقة | إشعار 15 دقيقة قبل الصلاة |
| `_daily_content_loop` | 6:00 صباحاً | إرسال حديث + حكمة + دعاء + مناجاة |
| `_event_check_loop` | 5:00 صباحاً | إشعار المناسبات الدينية |
| `_midnight_reset_loop` | 12:00 منتصف الليل | تصفير tracking المحتوى اليومي |
| `_tasbih_reminder_loop` | 9:00 مساءً | تذكير الأذكار المسائية |
| `_weekly_report_loop` | الأحد 7:00 صباحاً | تقرير أسبوعي للأدمن |
| `_content_health_loop` | 3:00 صباحاً | فحص سلامة ملفات المحتوى |
| `send_broadcast` | يدوي (أدمن) | بث رسالة لجميع المستخدمين |

**آلية الإرسال:** `safe_gather_send` → دفعات 25 رسالة/ثانية مع تأخير 1 ثانية بين الدفعات.

**ما ينقص:** لا شيء.

---

### `middleware/rate_limit.py` — 96 سطر ✅ (مُحدَّث لـ aiogram v3)
**الدور:** حماية البوت من الإغراق

| الحد | القيمة |
|---|---|
| الحد في الدقيقة | 20 رسالة |
| الحد في الساعة | 100 رسالة |
| إعفاء | ADMIN_IDS مُعفيون تلقائياً |

---

### `services/prayer_service.py` — 390 سطر ✅
**الدور:** حساب وتنسيق أوقات الصلاة

- `get_prayer_times(lat, lng, tz, city)` → يجلب من Aladhan API أو يحسب محلياً
- `get_next_prayer(...)` → يحسب الصلاة القادمة والوقت المتبقي
- `format_prayer_times(times, city)` → تنسيق للعرض
- `format_next_prayer(info)` → تنسيق الصلاة القادمة
- `get_prayer_taqibat(prayer)` → يقرأ ملف JSON للتعقيبات
- `format_taqibat_page(items, name, page, total)` → تنسيق صفحة التعقيبات

---

### `services/aladhan_service.py` — 130 سطر ✅
**الدور:** استدعاء Aladhan API لأوقات الصلاة الجعفرية

- يستخدم `aiohttp` لطلبات HTTP غير متزامنة
- يطبّق Method=1 (جعفري/اثني عشري)
- عند الفشل: يرجع `None` فتُستخدم الحسابات المحلية

---

### `services/content_service.py` — 231 سطر ✅
**الدور:** جلب وتنسيق المحتوى الديني من ملفات JSON

| الدالة | الوصف |
|---|---|
| `get_random_item(type, user_id)` | عنصر عشوائي لم يُرسَل للمستخدم سابقاً |
| `get_all_items(type)` | جميع عناصر نوع معين |
| `get_content_by_id(type, id)` | عنصر بالـ ID |
| `get_daily_content(type)` | محتوى اليوم |
| `get_random_content_for_subscription(sub, user_id)` | للـ scheduler |
| `format_hadith(item)` | تنسيق الحديث |
| `format_wisdom(item)` | تنسيق الحكمة |
| `format_dua(item)` | تنسيق الدعاء |
| `format_munajat(item)` | تنسيق المناجاة |
| `format_ziyarat(item)` | تنسيق الزيارة |

---

### `services/event_service.py` — 350 سطر ✅
**الدور:** إدارة المناسبات الدينية والتقويم الهجري

| الدالة | الوصف |
|---|---|
| `get_today_hijri()` | التاريخ الهجري اليوم (مع HIJRI_OFFSET) |
| `get_today_event()` | مناسبة اليوم (إن وُجدت) |
| `get_today_events_list()` | قائمة مناسبات اليوم |
| `get_upcoming_events(days)` | المناسبات خلال N يوماً |
| `get_weekly_dua()` | دعاء اليوم بحسب يوم الأسبوع |
| `get_weekly_ziyarat()` | زيارة اليوم بحسب يوم الأسبوع |
| `format_event(event)` | تنسيق المناسبة للعرض |
| `format_hijri_date(hijri)` | تنسيق التاريخ الهجري |
| `get_hijri_calendar()` | تقويم الشهر الهجري كاملاً |

---

### `services/navigation_service.py` — 268 سطر ✅ (مُحدَّث لـ aiogram v3)
**الدور:** بناء أزرار الـ InlineKeyboard لجميع القوائم

| الدالة | القائمة |
|---|---|
| `main_menu()` | القائمة الرئيسية (7 أزرار) |
| `ibadat_menu()` | العبادات اليومية (6 أزرار) |
| `taqibat_menu()` | تعقيبات الصلاة (5 أزرار) |
| `library_menu()` | المكتبة الدينية (6 أزرار) |
| `prayer_menu()` | الصلاة والأذان (5 أزرار) |
| `events_menu()` | المناسبات (5 أزرار) |
| `daily_menu()` | المحتوى اليومي (6 أزرار) |
| `settings_menu()` | الإعدادات (5 أزرار) |
| `subscriptions_settings_menu(subs)` | الاشتراكات (6 + رجوع) |
| `governorates_keyboard()` | اختيار المحافظة |
| `districts_keyboard(gov)` | اختيار القضاء |
| `pagination_buttons(items, prefix, page)` | تصفح القوائم |
| `taqibat_pagination_keyboard(prayer, page, total)` | تصفح التعقيبات |
| `content_actions_keyboard(type, id, back, is_fav)` | أزرار المحتوى (مفضلة + رجوع) |
| `favorites_menu()` | المفضلة (6 أزرار) |
| `back_button(target)` | زر رجوع بسيط |

---

### `services/subscription_service.py` — 84 سطر ✅
**الدور:** إدارة اشتراكات الإشعارات

| الاشتراك | الوصف |
|---|---|
| `hadith_daily` | حديث يومي |
| `wisdom_daily` | حكمة يومية |
| `dua_daily` | دعاء يومي |
| `munajat_daily` | مناجاة يومية |
| `prayer_reminder` | تذكير الصلاة |
| `event_reminder` | تذكير المناسبات |

---

### `services/location_data.py` — 159 سطر ✅
**الدور:** قاموس إحداثيات المدن العراقية (IRAQ_CITIES)

- يحتوي على المحافظات العراقية الرئيسية وأقضيتها
- كل مدينة لها `lat` و `lng`
- يُستخدم في اختيار الموقع اليدوي

---

### `clear_cache.py` — 15 سطر ✅
**الدور:** سكريبت يدوي لحذف كاش أوقات الصلاة من قاعدة البيانات

---

## 📂 ملفات البيانات (JSON)

### 📁 `data/normalized/daily_content/`

| الملف | الأسطر | العناصر | الحالة | الوصف |
|---|---|---|---|---|
| `hadith.json` | 38,469 | **2,564** ✅ | مكتمل | أحاديث من أهل البيت |
| `wisdom.json` | 300,201 | **21,442** ✅ | مكتمل | حِكَم ومواعظ |
| `daily_dua.json` | 188 | **30** ✅ | كافٍ | أدعية يومية (بعضها PDF) |
| `munajat.json` | 7 | **0** ❌ | **فارغ** | المناجيات اليومية |
| `wisdom_featured.json` | 7 | **0** ❌ | **فارغ** | الحِكَم المميّزة |
| `wisdom_deep.json` | 7 | **0** ❌ | **فارغ** | حِكَم مطوّلة |
| `wisdom_short.json` | 7 | **0** ❌ | **فارغ** | حِكَم قصيرة |

---

### 📁 `data/normalized/event_content/`

| الملف | الأسطر | العناصر | الحالة | الوصف |
|---|---|---|---|---|
| `events.json` | 990 | **140** ✅ | مكتمل | المناسبات الدينية الهجرية |
| `weekly_duas.json` | 85 | **7** ✅ | مكتمل | دعاء لكل يوم من الأسبوع |
| `weekly_ziyarat.json` | 58 | **7** ✅ | مكتمل | زيارة لكل يوم من الأسبوع |

---

### 📁 `data/normalized/library/`

| الملف | الأسطر | العناصر | الحالة | الوصف |
|---|---|---|---|---|
| `munajat.json` | 173 | **15** ✅ | كافٍ | المناجيات (المكتبة) |
| `ziyarat.json` | 128 | **20** ✅ | كافٍ | الزيارات (المكتبة) |
| `duas.json` | 7 | **0** ❌ | **فارغ** | أدعية المكتبة |
| `books.json` | 7 | **0** ❌ | **فارغ** | الكتب |
| `pdf_files.json` | 7 | **0** ❌ | **فارغ** | ملفات PDF |
| `pdf_library.json` | 14 | **0** ❌ | **فارغ** | مكتبة PDF |

---

### 📁 `data/normalized/prayer_content/`

| الملف | الأسطر | العناصر | الحالة | الوصف |
|---|---|---|---|---|
| `fajr.json` | 527 | **37** ✅ | مكتمل | تعقيبات صلاة الفجر |
| `dhuhr.json` | 457 | **32** ✅ | مكتمل | تعقيبات صلاة الظهر |
| `maghrib.json` | 429 | **30** ✅ | مكتمل | تعقيبات صلاة المغرب |
| `isha.json` | 345 | **24** ✅ | مكتمل | تعقيبات صلاة العشاء |

---

## ⚙️ ملفات الإعداد

| الملف | الأسطر | الوصف |
|---|---|---|
| `requirements.txt` | 6 | حزم Python (مُحدَّث لـ aiogram v3 + aiohttp ≥3.9) |
| `replit.nix` | 8 | تبعيات النظام (python312, aiohttp, gcc) |
| `.replit` | 39 | إعداد Replit (workflow، متغيرات البيئة) |
| `runtime.txt` | 0 | فارغ |
| `README.md` | 241 | توثيق المشروع الأصلي |

---

## 🗄️ ملف قاعدة البيانات

| الملف | الموقع | الوصف |
|---|---|---|
| `bot.db` | `storage/bot.db` | SQLite — يُنشَأ تلقائياً عند أول تشغيل |

---

## 🚦 ملخص حالة الملفات

### ✅ مكتمل ولا يحتاج تعديل
- `config.py` · `database.py` · `scheduler.py`
- `services/prayer_service.py` · `services/aladhan_service.py`
- `services/content_service.py` · `services/event_service.py`
- `services/subscription_service.py` · `services/location_data.py`
- بيانات: `hadith.json` · `wisdom.json` · `daily_dua.json`
- بيانات: `events.json` · `weekly_duas.json` · `weekly_ziyarat.json`
- بيانات: `fajr/dhuhr/maghrib/isha.json` (تعقيبات)

### ✅ مُحدَّث لـ aiogram v3
- `app.py` · `middleware/rate_limit.py` · `services/navigation_service.py`

### ✅ مجلد handlers/ — تم التحديث (aiogram v3)
- `handlers/` — مجلد مقسَّم بدلاً من الملف الواحد (1918 سطر) → 6 ملفات + `__init__.py`

### ❌ بيانات فارغة تحتاج محتوى
| الملف | ماذا ينقصه |
|---|---|
| `daily_content/munajat.json` | المناجيات اليومية |
| `daily_content/wisdom_featured.json` | أفضل الحِكَم المختارة |
| `daily_content/wisdom_short.json` | حِكَم قصيرة |
| `daily_content/wisdom_deep.json` | حِكَم مطوّلة |
| `library/duas.json` | نصوص أدعية المكتبة |
| `library/books.json` | الكتب |
| `library/pdf_files.json` | روابط ملفات PDF |
| `library/pdf_library.json` | مكتبة PDF |

---

## 🔑 المشكلة الرئيسية — تم حلها ✅

تم تحويل `handlers.py` الواحد (1918 سطر، aiogram v2) إلى مجلد `handlers/` مقسّم بأسلوب aiogram v3.

**الملف القديم:** `handlers_v2_backup.py` — نسخة احتياطية فقط من `handlers.py` الأصلي (v2)

**التغييرات المطبَّقة:**

```python
# v2 → v3 ✅ تم التطبيق
from aiogram import Dispatcher          →  from aiogram import Router
from aiogram.utils.exceptions import … →  from aiogram.exceptions import TelegramBadRequest
message.get_args()                      →  command: CommandObject (parameter)
dp.register_message_handler(fn, …)     →  @router.message(Command("start"))
dp.register_callback_query_handler(fn) →  @router.callback_query(F.data == "…")
ReplyKeyboardMarkup().add(…)           →  ReplyKeyboardMarkup(keyboard=[[…]])
InlineKeyboardMarkup().add(…)          →  InlineKeyboardMarkup(inline_keyboard=[[…]])
```
