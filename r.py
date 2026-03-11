import asyncio
import logging
import json
import os
import aiohttp
from datetime import datetime
from collections import Counter
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import BotCommand
from aiohttp import web

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8653073291:AAEZYYUIVROV37Hdx0Cr3ztuSnUhdZ8lzpg'
ADMIN_ID = 7951275068
DB_FILE = "friends_db.json"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- РАБОТА С ДАННЫМИ ---
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return set(json.load(f))
        except: return set()
    return set()

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(list(data), f)

FRIENDS = load_db()
last_solved_ids = {}
session = None

async def get_session():
    global session
    if session is None or session.closed:
        session = aiohttp.ClientSession()
    return session

async def fetch_cf(method, params=None):
    s = await get_session()
    url = f"https://codeforces.com/api/{method}"
    try:
        async with s.get(url, params=params, timeout=15) as resp:
            data = await resp.json()
            if data.get("status") == "OK":
                return data.get("result")
            return None
    except Exception as e:
        logger.error(f"CF API Error ({method}): {e}")
        return None

# --- ОБРАБОТЧИКИ КОМАНД ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        "🤖 **CF Spy Bot v2.0**\n\n"
        "Я слежу за активностью на Codeforces и помогаю расти.\n"
        "• Добавить друга: `/cf_follow ник`\n"
        "• Мои ошибки: `/weak ник`\n"
        "• Турниры: `/contests`"
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@dp.message(Command("cf_follow"))
async def cmd_follow(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("⚠️ Укажите ник: `/cf_follow tourist`")
    handle = command.args.strip()
    FRIENDS.add(handle)
    save_db(FRIENDS)
    await message.answer(f"✅ Теперь я слежу за <b>{handle}</b>", parse_mode="HTML")

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    if not FRIENDS:
        return await message.answer("❌ Список слежки пуст.")
    names = "\n".join([f"• `{h}`" for h in FRIENDS])
    await message.answer(f"👥 **В списке слежки:**\n{names}", parse_mode="Markdown")

@dp.message(Command("weak"))
async def cmd_weak(message: types.Message, command: CommandObject):
    handle = command.args.strip() if command.args else "tourist"
    await message.answer(f"🔎 Анализирую последние 100 попыток `{handle}`...", parse_mode="Markdown")
    res = await fetch_cf("user.status", {"handle": handle, "from": 1, "count": 100})
    if not res:
        return await message.answer("Не удалось получить данные. Проверь ник.")
    failed_tags = [tag for sub in res if sub['verdict'] != 'OK' for tag in sub['problem'].get('tags', [])]
    if not failed_tags:
        return await message.answer("🎉 Ошибок не найдено!")
    common = Counter(failed_tags).most_
