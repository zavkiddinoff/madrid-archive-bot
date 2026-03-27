import os
import psycopg2
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from flask import Flask
from threading import Thread

# --- RENDER PORT MASALASI ---
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- KONFIGURATSIYA ---
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

class AddMatch(StatesGroup):
    season, tournament, name, v360, v720, v1080 = State(), State(), State(), State(), State(), State()

def get_db():
    return psycopg2.connect(DATABASE_URL)

# --- TUGMALAR ---
def get_seasons_kb():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT DISTINCT season FROM matches ORDER BY season DESC")
    seasons = cur.fetchall(); cur.close(); conn.close()
    buttons = [[InlineKeyboardButton(text=s[0], callback_data=f"s:{s[0]}")] for s in seasons]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_tours_kb(season):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT DISTINCT tournament FROM matches WHERE season=%s", (season,))
    tours = cur.fetchall(); cur.close(); conn.close()
    buttons = [[InlineKeyboardButton(text=t[0], callback_data=f"t:{season}:{t[0]}")] for t in tours]
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_start")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_matches_kb(season, tour):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, match_name FROM matches WHERE season=%s AND tournament=%s", (season, tour))
    matches = cur.fetchall(); cur.close(); conn.close()
    buttons = [[InlineKeyboardButton(text=m[1], callback_data=f"m:{m[0]}")] for m in matches]
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"s:{season}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_quality_kb(m_id):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT season, tournament FROM matches WHERE id=%s", (m_id,))
    res = cur.fetchone(); cur.close(); conn.close()
    buttons = [
        [InlineKeyboardButton(text="📺 1080p", callback_data=f"v:{m_id}:v1080")],
        [InlineKeyboardButton(text="📺 720p", callback_data=f"v:{m_id}:v720")],
        [InlineKeyboardButton(text="📱 360p", callback_data=f"v:{m_id}:v360")]
    ]
    if res:
        buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"t:{res[0]}:{res[1]}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- HANDLERLAR ---
@dp.message(Command("start"), F.chat.type == "private")
async def start(msg: types.Message):
    await msg.answer("Hala Madrid! Real Madrid o'yinlari arxiviga xush kelibsiz.", reply_markup=get_seasons_kb())

@dp.callback_query(F.data == "back_start")
async def back_start(call: types.CallbackQuery):
    await call.message.edit_text("Mavsumni tanlang:", reply_markup=get_seasons_kb())

@dp.callback_query(F.data.startswith("s:"))
async def select_tour(call: types.CallbackQuery):
    season = call.data.split(":")[1]
    await call.message.edit_text(f"{season} - Turnirni tanlang:", reply_markup=get_tours_kb(season))

@dp.callback_query(F.data.startswith("t:"))
async def select_match(call: types.CallbackQuery):
    _, season, tour = call.data.split(":")
    await call.message.edit_text(f"{tour} - O'yinni tanlang:", reply_markup=get_matches_kb(season, tour))

@dp.callback_query(F.data.startswith("m:"))
async def select_quality(call: types.CallbackQuery):
    m_id = call.data.split(":")[1]
    await call.message.edit_text("Sifatni tanlang:", reply_markup=get_quality_kb(m_id))

@dp.callback_query(F.data.startswith("v:"))
async def send_video(call: types.CallbackQuery):
    _, m_id, quality = call.data.split(":")
    conn = get_db(); cur = conn.cursor()
    cur.execute(f"SELECT {quality}, match_name FROM matches WHERE id=%s", (m_id,))
    res = cur.fetchone(); cur.close(); conn.close()
    if res and res[0]:
        await call.message.answer_video(video=res[0], caption=f"🎬 {res[1]}\n\nHala Madrid!")
    else:
        await call.answer("Video topilmadi!", show_alert=True)

# --- ADMIN QISMI ---
@dp.message(Command("add"), F.from_user.id == ADMIN_ID)
async def add_start(msg: types.Message, state: FSMContext):
    await msg.answer("Mavsum (masalan: 2023/24):")
    await state.set_state(AddMatch.season)

@dp.message(AddMatch.season)
async def add_tour(msg: types.Message, state: FSMContext):
    await state.update_data(season=msg.text)
    await msg.answer("Turnir nomi:")
    await state.set_state(AddMatch.tournament)

@dp.message(AddMatch.tournament)
async def add_name(msg: types.Message, state: FSMContext):
    await state.update_data(tour=msg.text)
    await msg.answer("O'yin nomi:")
    await state.set_state(AddMatch.name)

@dp.message(AddMatch.name)
async def add_360(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("360p video yuboring:")
    await state.set_state(AddMatch.v360)

@dp.message(AddMatch.v360)
async def add_720(msg: types.Message, state: FSMContext, bot: Bot):
    v360 = msg.video.file_id if msg.video else msg.text
    await state.update_data(v360=v360)
    await msg.answer("720p video yuboring:")
    await state.set_state(AddMatch.v720)

@dp.message(AddMatch.v720)
async def add_1080(msg: types.Message, state: FSMContext):
    v720 = msg.video.file_id if msg.video else msg.text
    await state.update_data(v720=v720)
    await msg.answer("1080p video yuboring:")
    await state.set_state(AddMatch.v1080)

@dp.message(AddMatch.v1080)
async def add_finish(msg: types.Message, state: FSMContext):
    v1080 = msg.video.file_id if msg.video else msg.text
    d = await state.get_data()
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO matches (season, tournament, match_name, v360, v720, v1080) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                (d['season'], d['tour'], d['name'], d['v360'], d['v720'], v1080))
    new_id = cur.fetchone()[0]; conn.commit(); cur.close(); conn.close()
    await msg.answer(f"✅ O'yin qo'shildi! ID: `{new_id}`")
    await state.clear()

# --- ISHGA TUSHIRISH ---
async def main():
    Thread(target=run_flask).start() # Render uchun Flask
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
