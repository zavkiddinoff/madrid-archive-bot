import os
import logging
import threading
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

# Logging
logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
TOKEN      = os.environ["BOT_TOKEN"]
ADMIN_ID   = int(os.environ["ADMIN_ID"])
MONGO_URI  = os.environ["MONGO_URI"]

# MongoDB
client     = MongoClient(MONGO_URI)
db         = client["rmbot"]
collection = db["videos"]

flask_app  = Flask(__name__)
pending_upload: dict[int, str] = {}

@flask_app.route("/")
def health():
    return "✅ Bot ishlayapti!", 200

# DB Funksiyalar
def get_video(video_id: str):
    doc = collection.find_one({"_id": video_id})
    return doc["file_id"] if doc else None

def save_video(video_id: str, file_id: str):
    collection.update_one({"_id": video_id}, {"$set": {"file_id": file_id}}, upsert=True)

# Bot Handlers (Sizning buyruqlaringiz)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assalomu aleykum! 👋\nKerakli o'yin IDsini yuboring.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message: return
    user_id = update.effective_user.id

    # ADMIN: Video va ID saqlash
    if user_id == ADMIN_ID and message.video:
        pending_upload[user_id] = message.video.file_id
        await message.reply_text("✅ Video qabul qilindi! Endi ID kiriting.")
        return

    if user_id == ADMIN_ID and user_id in pending_upload and message.text:
        video_id = message.text.strip()
        save_video(video_id, pending_upload.pop(user_id))
        await message.reply_text(f"🏆 Saqlandi! ID: {video_id}")
        return

    # FOYDALANUVCHI: ID yuborganda video chiqarish
    if message.text:
        video_id = message.text.strip()
        file_id  = get_video(video_id)
        if file_id:
            await message.reply_video(video=file_id, caption=f"🏟 Arxiv\n🆔 ID: {video_id}")
        else:
            await message.reply_text("❌ Bunday ID topilmadi.")

# Flask Runner
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

# Main Async
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
