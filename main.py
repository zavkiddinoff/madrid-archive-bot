import os
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from upstash_redis import Redis

# --- SOZLAMALAR ---
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

# Upstash Redis ulanishi (Hech qanday IP ruxsati shart emas!)
redis = Redis(
    url=os.environ.get("UPSTASH_REDIS_REST_URL"), 
    token=os.environ.get("UPSTASH_REDIS_REST_TOKEN")
)

# --- RENDER UCHUN FLASK ---
flask_app = Flask(__name__)
@flask_app.route('/')
def health(): return "Bot Online!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

# --- BOT MANTIQI ---
waiting_video = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu aleykum, kerakli o'yin IDsini yuboring, "
        "IDlar ro'yxatini @losblancosuz_archive'dan topishingiz mumkin."
    )

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Admin video uchun ID yuborsa
    if user_id == ADMIN_ID and user_id in waiting_video:
        video_id = text.strip()
        file_id = waiting_video.pop(user_id)
        redis.set(video_id, file_id) # Bazaga saqlash
        await update.message.reply_text(f"✅ Saqlandi! ID: {video_id}")
        return

    # Foydalanuvchi ID yuborsa
    if text:
        video_id = text.strip()
        file_id = redis.get(video_id) # Bazadan qidirish
        if file_id:
            await update.message.reply_video(video=file_id)
        else:
            await update.message.reply_text("Afsus bunday video hozircha yo'q.")

async def handle_vid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        waiting_video[ADMIN_ID] = update.message.video.file_id
        await update.message.reply_text("🎬 Video qabul qilindi. Endi unga ID bering:")

# --- ASOSIY QISM ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_vid))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))

    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
