import os
import asyncio
import threading
import logging
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from upstash_redis import Redis

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- SOZLAMALAR ---
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

# Upstash Redis ulanishi
redis = Redis(
    url=os.environ.get("UPSTASH_REDIS_REST_URL"), 
    token=os.environ.get("UPSTASH_REDIS_REST_TOKEN")
)

# --- RENDER UCHUN FLASK (Health Check) ---
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

    # 1. ADMIN: Video uchun ID kiritganda
    if user_id == ADMIN_ID and user_id in waiting_video:
        video_id = text.strip()
        data = waiting_video.pop(user_id)
        
        # Video ID va Captionni birlashtirib saqlaymiz
        combined_value = f"{data['file_id']}|||{data['caption']}"
        redis.set(video_id, combined_value)
        
        await update.message.reply_text(f"✅ Video va uning matni saqlandi!\nID: {video_id}")
        return

    # 2. FOYDALANUVCHI: Video qidirganda
    if text:
        video_id = text.strip()
        raw_data = redis.get(video_id)
        
        if raw_data:
            # Agar ma'lumotda biz qo'shgan ajratuvchi bo'lsa
            if "|||" in str(raw_data):
                file_id, caption = str(raw_data).split("|||", 1)
                final_caption = caption if caption != "None" else ""
                await update.message.reply_video(video=file_id, caption=final_caption)
            else:
                # Eski videolar uchun (faqat file_id bo'lsa)
                await update.message.reply_video(video=str(raw_data))
        else:
            await update.message.reply_text("Afsus bunday video hozircha yo'q.")

async def handle_vid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Faqat admin video yuklay oladi
    if update.effective_user.id == ADMIN_ID:
        waiting_video[ADMIN_ID] = {
            "file_id": update.message.video.file_id,
            "caption": update.message.caption if update.message.caption else "None"
        }
        await update.message.reply_text("🎬 Video qabul qilindi. Endi ushbu video uchun ID (nom) yuboring:")

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    # Flaskni alohida oqimda ishga tushirish (Render o'chib qolmasligi uchun)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Botni yaratish
    app = Application.builder().token(TOKEN).build()
    
    # Handlerlarni qo'shish
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_vid))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))

    # Render-da RuntimeError bermasligi uchun asinxron tsikl
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        # Bot to'xtab qolmasligi uchun
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
