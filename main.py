import os
import logging
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

# ─── LOGGING VA SOZLAMALAR ──────────────────────────────────────────────────
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Render va MongoDB uchun kerakli o'zgaruvchilar
TOKEN      = os.environ.get("BOT_TOKEN")
ADMIN_ID   = int(os.environ.get("ADMIN_ID", 0))
MONGO_URI  = os.environ.get("MONGO_URI")

# MongoDB ulanishi
client     = MongoClient(MONGO_URI)
db         = client["madrid_archive"]
collection = db["videos"]

# Flask (Render botni o'chirib qo'ymasligi uchun "Health Check")
flask_app = Flask(__name__)
@flask_app.route('/')
def index(): return "Bot is running!", 200

# Admin yuklayotgan videoni vaqtincha ushlab turish uchun lug'at
waiting_for_id = {}

# ─── BOT FUNKSIYALARI ───────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start bosilganda chiqadigan xabar"""
    await update.message.reply_text(
        "Assalomu aleykum, kerakli o'yin IDsini yuboring, "
        "IDlar ro'yxatini @losblancosuz_archive'dan topishingiz mumkin."
    )

async def handle_admin_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin video yuborganda uni ushlab qoladi"""
    if update.effective_user.id != ADMIN_ID:
        return # Oddiy foydalanuvchi video yuborsa e'tibor bermaydi

    video_file_id = update.message.video.file_id
    waiting_for_id[ADMIN_ID] = video_file_id
    await update.message.reply_text("✅ Video qabul qilindi. Endi bu video uchun ID yuboring:")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ID yuborilganda videoni qidiradi yoki saqlaydi"""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Admin yangi video uchun ID yuborgan bo'lsa
    if user_id == ADMIN_ID and user_id in waiting_for_id:
        video_id = text
        file_id = waiting_for_id.pop(user_id)
        
        # Bazaga saqlash
        collection.update_one({"_id": video_id}, {"$set": {"file_id": file_id}}, upsert=True)
        await update.message.reply_text(f"🚀 Tayyor! Video '{video_id}' IDsi bilan saqlandi.")
        return

    # Foydalanuvchi ID yuborgan bo'lsa qidiruv
    result = collection.find_one({"_id": text})
    if result:
        await update.message.reply_video(video=result['file_id'])
    else:
        await update.message.reply_text("Afsus bunday video hozircha yo'q.")

# ─── ISHGA TUSHIRISH LOGIKASI ────────────────────────────────────────────────

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

async def main():
    # Flaskni fonda ishga tushiramiz
    threading.Thread(target=run_flask, daemon=True).start()

    # Botni qurish
    app = Application.builder().token(TOKEN).build()

    # Handlerlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_admin_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Render uchun asinxron polling
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
