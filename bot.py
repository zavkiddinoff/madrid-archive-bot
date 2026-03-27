import os
import psycopg2
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from flask import Flask  # Yangi qo'shildi
from threading import Thread # Yangi qo'shildi

# --- RENDER UCHUN SOXTA PORT (FLASK) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is active!"

def run_flask():
    # Render avtomatik PORT beradi, topolmasa 8080 ishlatadi
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- ASOSIY BOT SOZLAMALARI ---
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

class AddMatch(StatesGroup):
    season, tournament, name, v360, v720, v1080 = State(), State(), State(), State(), State(), State()

def get_db():
    return psycopg2.connect(DATABASE_URL)

# --- DINAMIK TUGMALAR ---
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
        [InlineKeyboardButton(text="📱 360p", callback_data=f"v:{m_id}:v360")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"t:{res[0]}:{res[1]}") if res else []]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ASOSIY HANDLERLAR ---
@dp.message(Command("start"), F.chat.type == "private")
async def start(msg: types.Message):
    start_text = (
        "Assalomu aleykum, men <a href='https://t.me/zavqiddinov_co'>Ilhomjon Zavqiddinov</a> tomonidan "
        "<a href='https://t.me/losblancosuzbekistan'>Los Blancos UZ</a> loyihasi uchun yaratilganman.\n\n"
        "Men orqali Real Madridning barcha o'yinlarini o'zbekcha sharhda topishingiz mumkin."
    )
    await msg.answer(start_text, parse_mode="HTML", reply_markup=get_seasons_kb(), disable_web_page_preview=True)

@dp.message(F.text.isdigit() & (F.chat.type == "private"))
async def search_by_code(msg: types.Message):
    match_id = msg.text
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT match_name FROM matches WHERE id=%s", (match_id,))
    res = cur.fetchone(); cur.close(); conn.close()
    
    if res:
        await msg.answer(f"🔍 Topildi: **{res[0]}**\nSifatni tanlang:", reply_markup=get_quality_kb(match_id))
    else:
        await msg.answer("❌ Bunday kodli o'yin topilmadi.")

# Callback'lar (Tugmalar bosilganda)
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
    await call.message.edit_text(f"{tour} - O'yinni tanlang:", reply
