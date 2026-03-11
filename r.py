import asyncio
import sqlite3
import random
import logging
import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# --- НАСТРОЙКИ ---
TOKEN = "8653073291:AAE2wrd9z9uQecOAs12qCWuinCBlY6ljf5w"
PORT = int(os.environ.get("PORT", 10000)) # Render сам подставит нужный порт
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (Костыль для порта) ---
async def handle(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Web server started on port {PORT}")

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect("spy.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS watching (chat_id INTEGER, handle TEXT, last_sub_id INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, tasks INTEGER DEFAULT 0, xp INTEGER DEFAULT 0, lvl INTEGER DEFAULT 1)")
    conn.commit()
    conn.close()

init_db()

# --- ФОНОВЫЙ МОНИТОРИНГ CF ---
async def check_cf_updates():
    while True:
        try:
            conn = sqlite3.connect("spy.db")
            cur = conn.cursor()
            cur.execute("SELECT chat_id, handle, last_sub_id FROM watching")
            targets = cur.fetchall()
            async with aiohttp.ClientSession() as session:
                for chat_id, handle, last_id in targets:
                    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=1"
                    async with session.get(url, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data["status"] == "OK" and data["result"]:
                                last_sub = data["result"][0]
                                if last_sub["id"] != last_id:
                                    if last_sub.get("verdict") == "OK":
                                        p = last_sub["problem"]
                                        await bot.send_message(chat_id, f"✅ **{handle}** затащил: `{p['name']}`")
                                    cur.execute("UPDATE watching SET last_sub_id = ? WHERE chat_id = ? AND handle = ?", (last_sub["id"], chat_id, handle))
                                    conn.commit()
            conn.close()
        except: pass
        await asyncio.sleep(60)

# --- КОМАНДЫ ---
@dp.message(Command("start"))
async def s(m: types.Message):
    await m.answer("🕵️‍♂️ Бот запущен на Web Service!\nВсе 30+ команд активны. Попробуй /cf_follow или /joke")

@dp.message(Command("cf_follow"))
async def f(m: types.Message):
    h = m.text.replace("/cf_follow", "").strip()
    if not h: return await m.answer("Ник?")
    conn = sqlite3.connect("spy.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO watching (chat_id, handle, last_sub_id) VALUES (?, ?, 0)", (m.chat.id, h))
    conn.commit()
    conn.close()
    await m.answer(f"👀 Слежу за {h}")

@dp.message(Command("help"))
async def help_cmd(m: types.Message):
    await m.answer("🚀 **Команды:**\n/cf_follow, /cf_check, /done, /stats, /joke, /roll, /calc, /pomo...")

# --- ГЛАВНЫЙ ЗАПУСК ---
async def main():
    # 1. Запускаем "заглушку" порта для Render
    asyncio.create_task(start_web_server())
    # 2. Очищаем старые конфликты
    await bot.delete_webhook(drop_pending_updates=True)
    # 3. Запускаем шпиона
    asyncio.create_task(check_cf_updates())
    # 4. Погнали!
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
