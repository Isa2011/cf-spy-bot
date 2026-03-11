import asyncio
import aiohttp
import logging
import json
import os
from collections import Counter
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
TOKEN = '8653073291:AAG7ztIMZfgzvfJPr_vXQy5qhvywMWbHbvM'
MY_CHAT_ID = 7951275068
JSON_FILE = "watchlist.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()
last_solved_ids = {}

# Загрузка WATCH_LIST
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r") as f: WATCH_LIST = json.load(f)
else: WATCH_LIST = []

async def get_cf(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as r: return await r.json()
        except: return None

# --- КОМАНДЫ АНАЛИТИКИ ---

@dp.message(Command("cf_progress"))
async def cf_progress(message: types.Message):
    args = message.text.split()
    handle = args[1] if len(args) > 1 else (WATCH_LIST[0] if WATCH_LIST else None)
    if not handle: return await message.answer("Укажи ник!")
    
    data = await get_cf(f"https://codeforces.com/api/user.status?handle={handle}")
    if data and data['status'] == 'OK':
        month_ago = datetime.now() - timedelta(days=30)
        solved_ratings = []
        for sub in data['result']:
            dt = datetime.fromtimestamp(sub['creationTimeSeconds'])
            if dt > month_ago and sub['verdict'] == 'OK':
                r = sub['problem'].get('rating')
                if r: solved_ratings.append(r)
        
        counts = Counter(solved_ratings)
        res = f"🧗 <b>Прогресс {handle} за 30 дней:</b>\n\n"
        for r in sorted(counts.keys()):
            res += f"• Рейтинг {r}: {counts[r]} шт.\n"
        res += f"\n✅ Всего решено: {len(solved_ratings)}"
        await message.answer(res, parse_mode="HTML")

@dp.message(Command("cf_compare"))
async def cf_compare(message: types.Message):
    args = message.text.split()
    if len(args) < 3: return await message.answer("Пиши: `/cf_compare ник1 ник2`", parse_mode="Markdown")
    
    u1, u2 = args[1], args[2]
    d1 = await get_cf(f"https://codeforces.com/api/user.info?handles={u1};{u2}")
    
    if d1 and d1['status'] == 'OK':
        res = "⚔️ <b>Сравнение игроков:</b>\n\n"
        for u in d1['result']:
            res += f"👤 <b>{u['handle']}</b>: {u.get('rating', 0)} ({u.get('rank', 'N/A')})\n"
        await message.answer(res, parse_mode="HTML")

@dp.message(Command("cf_contests"))
async def cf_contests(message: types.Message):
    data = await get_cf("https://codeforces.com/api/contest.list?gym=false")
    if data and data['status'] == 'OK':
        upcoming = [c for c in data['result'] if c['phase'] == 'BEFORE'][:5]
        res = "📅 <b>Ближайшие раунды:</b>\n\n"
        for c in upcoming:
            dt = datetime.fromtimestamp(c['startTimeSeconds']).strftime('%d.%m %H:%M')
            res += f"🏆 {c['name']}\n⏰ {dt}\n\n"
        await message.answer(res, parse_mode="HTML")

@dp.message(Command("cf_graph"))
async def cf_graph(message: types.Message):
    args = message.text.split()
    handle = args[1] if len(args) > 1 else (WATCH_LIST[0] if WATCH_LIST else None)
    if handle:
        url = f"https://cfviz.netlify.app/index.html?handle={handle}"
        await message.answer(f"📈 График и детальная визуализация для <b>{handle}</b>:\n{url}", parse_mode="HTML")

# --- СТАНДАРТНЫЕ КОМАНДЫ (из прошлого кода) ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🚀 <b>CF Ultra Bot активен!</b>\n\n"
        "🛰 <b>Слежка:</b> /cf_follow, /cf_list\n"
        "📊 <b>Анализ:</b> /cf_status, /cf_tags, /cf_weak\n"
        "📈 <b>Доп:</b> /cf_progress, /cf_compare, /cf_graph, /cf_contests",
        parse_mode="HTML"
    )

@dp.message(Command("cf_follow"))
async def cf_follow(message: types.Message):
    args = message.text.split()
    if len(args) > 1:
        h = args[1]
        if h not in WATCH_LIST:
            WATCH_LIST.append(h)
            with open(JSON_FILE, "w") as f: json.dump(WATCH_LIST, f)
            await message.answer(f"✅ Добавлен: {h}")

# --- ФОНОВАЯ СЛУЖБА (ШПИОН) ---
async def check_updates():
    async with aiohttp.ClientSession() as session:
        while True:
            for handle in WATCH_LIST.copy():
                try:
                    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=5"
                    async with session.get(url) as r:
                        data = await r.json()
                    if data.get('status') == 'OK':
                        for sub in data['result']:
                            if sub['verdict'] == 'OK':
                                s_id = sub['id']
                                if handle not in last_solved_ids:
                                    last_solved_ids[handle] = s_id; break
                                if s_id > last_solved_ids[handle]:
                                    p = sub['problem']
                                    m = f"🔥 <b>{handle}</b> решил: {p['name']} ({p.get('rating','?')})"
                                    await bot.send_message(MY_CHAT_ID, m, parse_mode="HTML")
                                    last_solved_ids[handle] = s_id
                except: pass
                await asyncio.sleep(2)
            await asyncio.sleep(60)

async def handle_root(request): return web.Response(text="Bot Alive")
async def main():
    app = web.Application()
    app.router.add_get('/', handle_root)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 10000).start()
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(check_updates())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
