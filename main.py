import os
import logging
import threading
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── Config ─────────────────────────────────────────────────────────────────
TOKEN      = os.environ["BOT_TOKEN"]
ADMIN_ID   = int(os.environ["ADMIN_ID"])
MONGO_URI  = os.environ["MONGO_URI"]

# ─── MongoDB ulanish ─────────────────────────────────────────────────────────
client     = MongoClient(MONGO_URI)
db         = client["rmbot"]
collection = db["videos"]

flask_app  = Flask(__name__)
pending_upload: dict[int, str] = {}   # admin_id → file_id


# ─── Flask health-check ──────────────────────────────────────────────────────
@flask_app.route("/")
def health():
    return "✅ Real Madrid Arxiv Bot ishlayapti!", 200

# ─── Video DB funksiyalari ───────────────────────────────────────────────────
def get_video(video_id: str) -> str | None:
    doc = collection.find_one({"_id": video_id})
    return doc["file_id"] if doc else None

def save_video(video_id: str, file_id: str) -> None:
    collection.update_one(
        {"_id": video_id},
        {"$set": {"file_id": file_id}},
        upsert=True
    )
    logger.info(f"Video saqlandi: ID={video_id}")

def delete_video(video_id: str) -> bool:
    result = collection.delete_one({"_id": video_id})
    return result.deleted_count > 0

def count_videos() -> int:
    return collection.count_documents({})

def list_all_videos() -> list:
    return [doc["_id"] for doc in collection.find({}, {"_id": 1})]


# ─── /start ─────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu aleykum! 👋⚽\n\n"
        "Kerakli o'yin IDsini yuboring.\n\n"
        "📋 IDlar ro'yxatini @losblancosuz_archive dan topishingiz mumkin."
    )


# ─── /list (faqat admin) ─────────────────────────────────────────────────────
async def list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    ids = list_all_videos()
    if not ids:
        await update.message.reply_text("📭 Hozircha hech qanday video yo'q.")
        return

    text = f"📦 Jami videolar: <b>{len(ids)}</b>\n\n"
    text += "\n".join(f"• <code>{vid_id}</code>" for vid_id in ids)
    await update.message.reply_text(text, parse_mode="HTML")


# ─── /delete (faqat admin) ───────────────────────────────────────────────────
async def delete_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "❗ Foydalanish: <code>/delete video_id</code>",
            parse_mode="HTML"
        )
        return

    video_id = context.args[0].strip()
    if delete_video(video_id):
        await update.message.reply_text(
            f"🗑 <code>{video_id}</code> o'chirildi.",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            f"❌ <code>{video_id}</code> topilmadi.",
            parse_mode="HTML"
        )


# ─── Asosiy handler ─────────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    user_id = update.effective_user.id

    # ── ADMIN: video yubordi ─────────────────────────────────────────────────
    if user_id == ADMIN_ID and message.video:
        file_id = message.video.file_id
        pending_upload[user_id] = file_id
        await message.reply_text(
            "✅ Video qabul qilindi!\n\n"
            "🆔 Endi bu video uchun <b>ID</b> kiriting\n"
            "(masalan: <code>rm_vs_barca_2006</code>):\n\n"
            "⚠️ Agar bu IDdagi video allaqachon mavjud bo'lsa, <b>ustidan yoziladi</b>.",
            parse_mode="HTML"
        )
        return

    # ── ADMIN: ID kiritayapti ────────────────────────────────────────────────
    if user_id == ADMIN_ID and user_id in pending_upload and message.text:
        video_id = message.text.strip()

        if not video_id:
            await message.reply_text("❗ ID bo'sh bo'lishi mumkin emas.")
            return

        file_id = pending_upload.pop(user_id)
        save_video(video_id, file_id)

        await message.reply_text(
            f"🏆 Muvaffaqiyatli saqlandi!\n\n"
            f"🆔 ID: <code>{video_id}</code>\n"
            f"📦 Jami videolar: <b>{count_videos()}</b>",
            parse_mode="HTML"
        )
        return

    # ── FOYDALANUVCHI: ID yubordi ────────────────────────────────────────────
    if message.text:
        video_id = message.text.strip()
        file_id  = get_video(video_id)

        if file_id:
            await message.reply_video(
                video=file_id,
                caption=(
                    f"🏟 <b>Real Madrid Arxiv</b>\n"
                    f"🆔 ID: <code>{video_id}</code>\n\n"
                    f"📺 @losblancosuzbekistan"
                ),
                parse_mode="HTML"
            )
        else:
            await message.reply_text(
                "❌ Bunday ID topilmadi.\n\n"
                "📋 IDlar ro'yxatini @losblancosuz_archive dan tekshiring.\n"
                "⚠️ Katta-kichik harflarga e'tibor bering!"
            )
        return

    if user_id != ADMIN_ID:
        await message.reply_text(
            "Iltimos, o'yin IDsini matn ko'rinishida yuboring. 📝\n"
            "IDlar ro'yxati: @losblancosuz_archive"
        )


# ─── Flask runner ───────────────────────────────────────────────────────────
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    # use_reloader=False Render va threading uchun shart
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)


# ─── Main (Yangilangan asinxron qism) ────────────────────────────────────────
async def main_async():
    # Flaskni alohida threadda ishga tushirish
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask health server ishga tushdi.")

    # Botni qurish
    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    # Handlerlarni qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list_videos))
    application.add_handler(CommandHandler("delete", delete_cmd))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    logger.info("Bot polling rejimida ishga tushdi!")
    
    # Asinxron ishga tushirish
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        
        # Bot to'xtab qolmasligi uchun event loopni ochiq saqlash
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        # Yangi Python versiyalarida event loopni ishga tushirishning eng to'g'ri yo'li
        asyncio.run(main_async())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
    except Exception as e:
        logger.error(f"Kutilmagan xatolik: {e}")
