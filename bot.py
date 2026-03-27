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

# --- RENDER PORT VA FLASK (Bot o'chib qolmasligi uchun) ---
app = Flask('')
@app.route('/')
def home(): return "Hala Madrid!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- KONFIGURATSIYA (Render Environment Variables dan oladi) ---
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

# --- FSM (Ma'lumot qo'shish bosqichlari) ---
class AddMatch(StatesGroup):
    season = State()
    tournament = State()
    match_name = State()
    v360 = State()
    v720 = State()
    v1080 = State()

def get_db():
    return psycopg2.connect(DATABASE_URL)

# --- TUGMALAR (Keyboard) ---
def get_seasons_kb():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT DISTINCT season FROM matches ORDER BY season DESC")
    seasons = cur.fetchall(); cur.close(); conn.close()
    buttons = [[InlineKeyboardButton(text=f"📅 {s[0]}", callback_data=f"s:{s[0]}")] for s in seasons]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_tours_kb(season):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT DISTINCT tournament FROM matches WHERE season=%s", (season,))
    tours = cur.fetchall(); cur.close(); conn.close()
    buttons = [[InlineKeyboardButton(text=f"🏆 {t[0]}", callback_data=f"t:{season}:{t[0]}")] for t in tours]
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_start")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_matches_kb(season, tour):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, match_name FROM matches WHERE season=%s AND tournament=%s", (season, tour))
    matches = cur.fetchall(); cur.close(); conn.close()
    buttons = [[InlineKeyboardButton(text=f"⚽️ {m[1]}", callback_data=f"m:{m[0]}")] for m in matches]
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"s:{season}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_quality_kb(m_id):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT season, tournament FROM matches WHERE id=%s", (m_id,))
    res = cur.fetchone(); cur.close(); conn.close()
    buttons = [
        [InlineKeyboardButton(text="📺 1080p (Full HD)", callback_data=f"v:{m_id}:v1080")],
        [InlineKeyboardButton(text="📺 720p (HD)", callback_data=f"v:{m_id}:v720")],
        [InlineKeyboardButton(text="📱 360p (Mobil)", callback_data=f"v:{m_id}:v360")]
    ]
    if res:
        buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"t:{res[0]}:{res[1]}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- HANDLERLAR ---

@dp.message(Command("start"), F.chat.type == "private")
async def start(msg: types.Message):
    # Real Madrid logosi stikeri (agar bu ID ishlamasa, boshqa stiker yuboring)
    await msg.answer_sticker("CAACAgIAAxkBAAEL6_hl-4hB5yX-H8fQzN8Y6I8Y8Y8Y8AAOFAAC_V7ID_S-H8Y8Y8Y8Y8Y8")
    
    text = (
        "Assalomu aleykum! 👋\n\n"
        "Men
