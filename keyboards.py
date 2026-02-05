from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Foydalanuvchi menyusi
user_menu = ReplyKeyboardMarkup(resize_keyboard=True)
user_menu.add(
    KeyboardButton("➕ Trek qo‘shish"),
    KeyboardButton("📋 Treklarim")
)
user_menu.add(
    KeyboardButton("💳 To‘lov"),
    KeyboardButton("📍 Olib ketish"),
    KeyboardButton("🆘 Yordam")
)

# Admin menyusi
admin_menu = ReplyKeyboardMarkup(resize_keyboard=True)
admin_menu.add(
    KeyboardButton("📋 Barcha treklar"),
    KeyboardButton("⚙️ Trek boshqaruv"),
    KeyboardButton("🔍 Trek qidirish")
)

# Inline tugmalar trek boshqarish uchun
def track_manage_keyboard(track_code):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("Holat ✅", callback_data=f"status_{track_code}"),
        InlineKeyboardButton("To‘lov 💰", callback_data=f"paid_{track_code}")
    )
    kb.add(
        InlineKeyboardButton("Olib ketish 📍", callback_data=f"pickup_{track_code}")
    )
    return kb
