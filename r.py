import asyncio
import logging
import json
import os
import aiohttp
import random
from datetime import datetime, timedelta
from collections import Counter
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from aiogram.types import BotCommand
from aiohttp import web

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8653073291:AAEZYYUIVROV37Hdx0Cr3ztuSnUhdZ8lzpg'
ADMIN_ID = 7951275068
DB_FILE = "friends_db.json"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
session_container = {"session": None}

async def get_session():
    if session_container["session"] is None or session_container["session"].closed:
        session_container["session"] = aiohttp.ClientSession()
    return session_container["session"]

async def fetch_cf(method, params=None):
    s = await get_session()
    url = f"https://codeforces.com/api/{method}"
    try:
        async with s.get(url, params=params, timeout=15) as resp:
            data = await resp.json()
            return data.get("result") if data.get("status") == "OK" else None
    except Exception as e:
        logger.error(f"CF API Error ({method}): {e}")
        return None

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ОБРАБОТЧИКИ КОМАНД ---

@dp.message(Command("start", "help"))
async def cmd_help(message: types.Message):
    help_text = (
        "🚀 <b>CF Spy Bot Professional</b>\n\n"
        "<b>Основные:</b>\n"
        "➕ /cf_follow <code>ник</code> | ➖ /remove <code>ник</code>\n"
        "📋 /list — Кто в списке\n\n"
        "<b>Аналитика:</b>\n"
        "👤 /profile <code>ник</code> — Инфо\n"
        "📊 /weak <code>ник</code> — Слабые темы\n"
        "🔥 /streak <code>ник</code> — Ударный режим\n"
        "🛠 /upsolve <code>ник</code> — Что нужно дорешать\n\n"
        "<b>Битва и Тренировки:</b>\n"
        "⚔️ /versus <code>н1 н2</code> — Сравнение\n"
        "🎲 /pick <code>рейтинг</code> — Случайная задача\n"
        "📅 /contests — Расписание"
    )
    await message.answer(help_text, parse_mode="HTML")

@dp.message(Command("streak"))
async def cmd_streak(message: types.Message, command: CommandObject):
    handle = command.args.strip() if command.args else "Alihan_7"
    res = await fetch_cf("user.status", {"handle": handle, "from": 1, "count": 500})
    if not res: return await message.answer("Ошибка данных.")
    
    solved_dates = set()
    for sub in res:
        if sub['verdict'] == 'OK':
            dt = datetime.fromtimestamp(sub['creationTimeSeconds']).date()
            solved_dates.add(dt)
    
    streak = 0
    curr = datetime.now().date()
    while curr in solved_dates:
        streak += 1
        curr -= timedelta(days=1)
    
    await message.answer(f"🔥 У <b>{handle}</b> ударный режим: <b>{streak} дней</b>!", parse_mode="HTML")

@dp.message(Command("upsolve"))
async def cmd_upsolve(message: types.Message, command: CommandObject):
    handle = command.args.strip() if command.args else "Alihan_7"
    res = await fetch_cf("user.status", {"handle": handle, "from": 1, "count": 100})
    if not res: return await message.answer("Ошибка API.")
    
    attempted = {}
    solved = set()
    for sub in res:
        p_id = f"{sub['problem']['contestId']}{sub['problem']['index']}"
        if sub['verdict'] == 'OK':
            solved.add(p_id)
        else:
            attempted[p_id] = sub['problem']
            
    to_upsolve = [p for p_id, p in attempted.items() if p_id not in solved]
    if not to_upsolve:
        return await message.answer("✅ Всё дорешано! Красава.")
    
    text = "🛠 <b>Нужно дорешать:</b>\n\n"
    for p in to_upsolve[:5]:
        text += f"• {p['name']} ({p.get('rating', '???')}) <a href='https://codeforces.com/contest/{p['contestId']}/problem/{p['index']}'>🔗 Ссылка</a>\n"
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

@dp.message(Command("cf_follow"))
async def cmd_follow(message: types.Message, command: CommandObject):
    if not command.args: return await message.answer("⚠️ Пиши: /cf_follow tourist")
    handle = command.args.strip()
    FRIENDS.add(handle)
    save_db(FRIENDS)
    await message.answer(f"✅ Теперь я шпионю за <b>{handle}</b>", parse_mode="HTML")

@dp.message(Command("remove"))
async def cmd_remove(message: types.Message, command: CommandObject):
    if not command.args: return await message.answer("⚠️ Пиши: /remove ник")
    handle = command.args.strip()
    if handle in FRIENDS:
        FRIENDS.remove(handle)
        save_db(FRIENDS)
        await message.answer(f"❌ Больше не слежу за <b>{handle}</b>", parse_mode="HTML")

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    if not FRIENDS: return await message.answer("Список пуст.")
    names = "\n".join([f"• <code>{h}</code>" for h in FRIENDS])
    await message.answer(f"👥 <b>В списке слежки:</b>\n{names}", parse_mode="HTML")

@dp.message(Command("profile"))
async def cmd_profile(message: types.Message, command: CommandObject):
    handle = command.args.strip() if command.args else "Alihan_7"
    res = await fetch_cf("user.info", {"handles": handle})
    if not res: return await message.answer("Пользователь не найден.")
    u = res[0]
    text = (f"👤 <b>Профиль: {u['handle']}</b>\n"
            f"🏆 Ранг: {u.get('rank', 'N/A')}\n"
            f"📈 Рейтинг: {u.get('rating', 0)} (max: {u.get('maxRating', 0)})\n"
            f"🌍 Страна: {u.get('country', 'N/A')}")
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("weak"))
async def cmd_weak(message: types.Message, command: CommandObject):
    handle = command.args.strip() if command.args else "Alihan_7"
    res = await fetch_cf("user.status", {"handle": handle, "from": 1, "count": 100})
    if not res: return await message.answer("Ошибка.")
    tags = [t for s in res if s['verdict'] != 'OK' for t in s['problem'].get('tags', [])]
    common = Counter(tags).most_common(5)
    report = "\n".join([f"🔸 {tag}: {c} раз" for tag, c in common])
    await message.answer(f"📊 <b>Слабые темы {handle}:</b>\n\n{report}", parse_mode="HTML")

@dp.message(Command("pick"))
async def cmd_pick(message: types.Message, command: CommandObject):
    r = command.args.strip() if command.args else "1200"
    res = await fetch_cf("problemset.problems")
    if not res: return await message.answer("Ошибка.")
    probs = [p for p in res['problems'] if str(p.get('rating')) == r]
    if not probs: return await message.answer("Нет таких задач.")
    p = random.choice(probs)
    url = f"https://codeforces.com/contest/{p['contestId']}/problem/{p['index']}"
    await message.answer(f"🎲 <b>Задача ({r}):</b>\n{p['name']}\n🔗 <a href='{url}'>Открыть</a>", parse_mode="HTML")

@dp.message(Command("versus"))
async def cmd_versus(message: types.Message, command: CommandObject):
    if not command.args or len(command.args.split()) < 2: return await message.answer("Надо 2 ника.")
    h1, h2 = command.args.split()[:2]
    r1, r2 = await fetch_cf("user.info", {"handles": h1}), await fetch_cf("user.info", {"handles": h2})
    if r1 and r2:
        u1, u2 = r1[0], r2[0]
        winner = h1 if u1.get('rating',0) > u2.get('rating',0) else h2
        await message.answer(f"⚔️ <b>{h1} ({u1.get('rating',0)}) vs {h2} ({u2.get('rating',0)})</b>\n\nПобеждает: {winner} 🔥", parse_mode="HTML")

@dp.message(Command("contests"))
async def cmd_contests(message: types.Message):
    res = await fetch_cf("contest.list", {"gym": "false"})
    upcoming = [c for c in res if c['phase'] == 'BEFORE'][::-1]
    text = "📅 <b>Ближайшие раунды:</b>\n\n"
    for c in upcoming[:4]: text += f"🏆 {c['name']}\n\n"
    await message.answer(text, parse_mode="HTML")

# --- МОНИТОРИНГ ---
async def checker():
    await asyncio.sleep(10)
    while True:
        for handle in list(FRIENDS):
            res = await fetch_cf("user.status", {"handle": handle, "from": 1, "count": 1})
            if res and res[0]['verdict'] == 'OK':
                s_id = res[0]['id']
                if handle not in last_solved_ids: last_solved_ids[handle] = s_id
                elif last_solved_ids[handle] != s_id:
                    last_solved_ids[handle] = s_id
                    p = res[0]['problem']
                    msg = (f"🔥 <b>{handle}</b> решил задачу!\n\n"
                           f"📝 {p['name']} ({p.get('rating', '???')})\n"
                           f"🔗 <a href='https://codeforces.com/contest/{res[0].get('contestId')}/problem/{p['index']}'>Открыть</a>")
                    try: await bot.send_message(ADMIN_ID, msg, parse_mode="HTML")
                    except: pass
            await asyncio.sleep(2)
        await asyncio.sleep(60)

async def handle_web(request): return web.Response(text="Bot is running")

async def main():
    app = web.Application(); app.router.add_get("/", handle_web)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", 10000).start()
    await bot.set_my_commands([
        BotCommand(command="help", description="Все команды"),
        BotCommand(command="cf_follow", description="Следить за ником"),
        BotCommand(command="streak", description="Ударный режим"),
        BotCommand(command="upsolve", description="Дорешивание"),
        BotCommand(command="pick", description="Случайная задача")
    ])
    asyncio.create_task(checker())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
