from aiogram import Bot, Dispatcher, executor, types
from config import BOT_TOKEN, ADMINS, PAYME_MERCHANT_ID, PAYME_SECRET_KEY, PAYME_CALLBACK_URL
from keyboards import user_menu, admin_menu, track_manage_keyboard
import sqlite3
import requests
import uuid
import hmac
import hashlib
import json

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

db = sqlite3.connect("cargo.db")
cursor = db.cursor()

# --- /START ---
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    cursor.execute("INSERT OR IGNORE INTO users (tg_id) VALUES (?)", (msg.from_user.id,))
    db.commit()
    
    if msg.from_user.id in ADMINS:
        await msg.answer("👮 Admin menyu", reply_markup=admin_menu)
    else:
        await msg.answer("📦 Cargo botga xush kelibsiz!", reply_markup=user_menu)

# --- FOYDALANUVCHI FUNKSIYALARI ---

@dp.message_handler(text="➕ Trek qo‘shish")
async def add_track(msg: types.Message):
    await msg.answer("✍️ Trek raqamni yuboring:")

@dp.message_handler(lambda m: len(m.text) > 5)
async def save_track(msg: types.Message):
    cursor.execute("SELECT id FROM users WHERE tg_id=?", (msg.from_user.id,))
    user_id = cursor.fetchone()[0]
    
    cursor.execute("INSERT INTO tracks (user_id, track_code) VALUES (?,?)", (user_id, msg.text))
    db.commit()
    await msg.answer("✅ Trek qo‘shildi")

@dp.message_handler(text="📋 Treklarim")
async def my_tracks(msg: types.Message):
    cursor.execute("""
    SELECT track_code, status, price, weight, paid, pickup_point FROM tracks
    JOIN users ON users.id = tracks.user_id
    WHERE users.tg_id=?
    """, (msg.from_user.id,))
    rows = cursor.fetchall()
    
    if not rows:
        await msg.answer("📭 Treklar yo‘q")
        return
    
    text = ""
    for t in rows:
        text += f"""
📦 {t[0]}
Holat: {t[1]}
💰 Narx: {t[2]} so'm
⚖️ Og‘irlik: {t[3]} kg
To‘lov: {"✅" if t[4] else "❌"}
Olib ketish: {t[5]}
        """
    await msg.answer(text)

# 💳 To‘lov (Payme)
@dp.message_handler(text="💳 To‘lov")
async def pay_track(msg: types.Message):
    await msg.answer("💰 To‘lov qilmoqchi bo‘lgan trek raqamini kiriting:")

@dp.message_handler(lambda m: m.text.startswith("TR"))
async def mark_paid(msg: types.Message):
    cursor.execute("SELECT price FROM tracks WHERE track_code=? AND user_id=(SELECT id FROM users WHERE tg_id=?)", (msg.text, msg.from_user.id))
    res = cursor.fetchone()
    if not res or res[0] <= 0:
        await msg.answer("❌ Trek topilmadi yoki narx belgilanmadi.")
        return
    price = res[0]
    invoice_id = str(uuid.uuid4())
    data = {
        "amount": price,
        "account": msg.text,
        "merchant_id": PAYME_MERCHANT_ID,
        "merchant_key": PAYME_SECRET_KEY,
        "callback_url": PAYME_CALLBACK_URL,
        "invoice_id": invoice_id
    }
    # HMAC signature
    sign = hmac.new(PAYME_SECRET_KEY.encode(), msg.text.encode(), hashlib.sha256).hexdigest()
    payment_url = f"https://checkout.payme.uz?invoice={invoice_id}&signature={sign}"
    await msg.answer(f"💳 To‘lov uchun link:\n{payment_url}")

# 📍 Olib ketish punkti
@dp.message_handler(text="📍 Olib ketish")
async def pickup(msg: types.Message):
    await msg.answer("Olib ketish punktini tanlang (Pochta / Punkt):")

@dp.message_handler(lambda m: m.text.lower() in ["pochta", "punkt"])
async def set_pickup(msg: types.Message):
    cursor.execute("UPDATE tracks SET pickup_point=? WHERE user_id=(SELECT id FROM users WHERE tg_id=?)", (msg.text.capitalize(), msg.from_user.id))
    db.commit()
    await msg.answer(f"📍 Olib ketish punktingiz {msg.text.capitalize()} deb belgilandi")

# 🆘 Yordam
@dp.message_handler(text="🆘 Yordam")
async def help_user(msg: types.Message):
    await msg.answer("📌 Foydalanish:\n➕ Trek qo‘shish\n📋 Treklarim\n💳 To‘lov\n📍 Olib ketish")

# --- ADMIN FUNKSIYALARI ---
@dp.message_handler(text="📋 Barcha treklar")
async def all_tracks(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return
    cursor.execute("SELECT track_code, status, price, weight, paid, pickup_point FROM tracks")
    rows = cursor.fetchall()
    
    text = ""
    for t in rows:
        text += f"""
📦 {t[0]}
Holat: {t[1]}
💰 Narx: {t[2]} so'm
⚖️ {t[3]} kg
To‘lov: {"✅" if t[4] else "❌"}
Olib ketish: {t[5]}
        """
    await msg.answer(text)

@dp.message_handler(text="⚙️ Trek boshqaruv")
async def manage_tracks(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return
    cursor.execute("SELECT track_code FROM tracks")
    rows = cursor.fetchall()
    for t in rows:
        await msg.answer(f"📦 {t[0]}", reply_markup=track_manage_keyboard(t[0]))

# Inline tugmalar uchun callback
@dp.callback_query_handler(lambda c: True)
async def process_callback(call):
    data = call.data.split("_")
    action, track_code = data[0], "_".join(data[1:])
    
    if action == "status":
        cursor.execute("SELECT status FROM tracks WHERE track_code=?", (track_code,))
        current = cursor.fetchone()[0]
        statuses = ["Yolda", "Yetib keldi", "Topshirildi"]
        new_index = (statuses.index(current)+1)%len(statuses)
        cursor.execute("UPDATE tracks SET status=? WHERE track_code=?", (statuses[new_index], track_code))
        db.commit()
        await call.message.edit_text(f"📦 {track_code}\nHolat: {statuses[new_index]}", reply_markup=track_manage_keyboard(track_code))

    elif action == "paid":
        cursor.execute("SELECT paid FROM tracks WHERE track_code=?", (track_code,))
        current = cursor.fetchone()[0]
        new = 0 if current else 1
        cursor.execute("UPDATE tracks SET paid=? WHERE track_code=?", (new, track_code))
        db.commit()
        await call.message.edit_text(f"📦 {track_code}\nTo‘lov: {'✅' if new else '❌'}", reply_markup=track_manage_keyboard(track_code))

    elif action == "pickup":
        cursor.execute("SELECT pickup_point FROM tracks WHERE track_code=?", (track_code,))
        current = cursor.fetchone()[0]
        new = "Pochta" if current == "Punkt" else "Punkt"
        cursor.execute("UPDATE tracks SET pickup_point=? WHERE track_code=?", (new, track_code))
        db.commit()
        await call.message.edit_text(f"📦 {track_code}\nOlib ketish: {new}", reply_markup=track_manage_keyboard(track_code))
    
    await call.answer()

# Trek qidirish
@dp.message_handler(text="🔍 Trek qidirish")
async def search_track(msg: types.Message):
    await msg.answer("Qidiriladigan trek raqamini kiriting:")

@dp.message_handler(lambda m: True)
async def find_track(msg: types.Message):
    cursor.execute("SELECT track_code, status, price, weight, paid, pickup_point FROM tracks WHERE track_code LIKE ?", (f"%{msg.text}%",))
    rows = cursor.fetchall()
    if not rows:
        await msg.answer("❌ Trek topilmadi")
        return
    text = ""
    for t in rows:
        text += f"""
📦 {t[0]}
Holat: {t[1]}
💰 Narx: {t[2]}
⚖️ Og‘irlik: {t[3]} kg
To‘lov: {"✅" if t[4] else "❌"}
Olib ketish: {t[5]}
        """
    await msg.answer(text)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
