"""
Athar Shia Bot - Configuration
بوت آثار الشيعة - ملف الإعدادات
"""

import os

# ─── Bot Token ───
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ─── Admin Settings ───
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))

# ─── Channel Settings ───
CHANNEL_ID = os.getenv("CHANNEL_ID", "@your_channel")

# ─── Location & Prayer Times ───
TIMEZONE = os.getenv("TIMEZONE", "Asia/Baghdad")
CITY = os.getenv("CITY", "بغداد")
LATITUDE = float(os.getenv("LATITUDE", "33.3152"))
LONGITUDE = float(os.getenv("LONGITUDE", "44.3661"))

# ─── Calculation Method ───
# 1: Jafari/Ithna Ashari (Shia)
# 2: University of Islamic Sciences, Karachi
# 3: Islamic Society of North America
# 4: Muslim World League
# 5: Umm al-Qura
PRAYER_METHOD = int(os.getenv("PRAYER_METHOD", "1"))

# ─── Content Settings ───
MAX_DAILY_CONTENT = int(os.getenv("MAX_DAILY_CONTENT", "3"))
ENABLE_SUBSCRIPTIONS = os.getenv("ENABLE_SUBSCRIPTIONS", "true").lower() == "true"

# ─── Messages ───
WELCOME_MESSAGE = """
📿 <b>أهلاً وسهلاً بك في بوت آثار</b>

البوت الرفيق اليومي لمتابعة:
• الأدعية والزيارات والمناجيات
• مواقيت الصلاة والتعقيبات
• المناسبات الدينية والأعمال
• المحتوى اليومي (حديث، حكمة، دعاء)

اختر من القائمة أدناه 👇
"""

ABOUT_MESSAGE = """
📿 <b>بوت آثار - Athar Bot</b>

مكتبة دينية ومرافق يومي للمستخدم الشيعي.

الميزات:
• مكتبة شاملة للأدعية والزيارات والمناجيات
• مواقيت الصلاة والتعقيبات
• المناسبات الهجرية والأعمال
• المحتوى اليومي المتجدد
• نظام اشتراكات ذكي

📎 <b>ملاحظة:</b> البوت يعتمد على ملفات JSON منظمة،
قابلة للتوسعة دون تعديل الكود.

🤖 <b>الإصدار:</b> 1.0.0
"""
