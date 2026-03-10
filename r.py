import asyncio
import aiohttp
import logging
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# --- ВКЛЮЧАЕМ ЛОГИ (Режим рентгена) ---
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

TOKEN = '8653073291:AAG7ztIMZfgzvfJPr_vXQy5qhvywMWbHbvM'
MY_CHAT_ID = 7951275068
WATCH_LIST = ['Alihan_7', 'NullPhase', 'whyy', 'matanov']

bot = Bot(token=TOKEN)
dp = Dispatcher()
last_solved_ids = {}

# --- КОСТЫЛЬ ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()

# --- ОБРАБОТЧИКИ КОМАНД ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    print(f"🔥 ПОЛУЧЕНА КОМАНДА /start от {message.from_user.id}", flush=True)
    await message.answer("🕵️‍♂️ Бот-шпион запущен!\nЯ слежу за Codeforces.")

@dp.message(Command("check"))
async def cmd_check(message: types.Message):
    await message.answer(f"✅ Я работаю!\nСлежу за: {', '.join(WATCH_LIST)}")

# --- ЛОГИКА ШПИОНА ---
async def check_updates():
    async with aiohttp.ClientSession() as session:
        while True:
            for handle in WATCH_LIST:
                try:
                    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=5"
                    async with session.get(url) as resp:
                        data = await resp.json()
                    if data.get('status') == 'OK':
                        for sub in data['result']:
                            if sub['verdict'] == 'OK':
                                s_id = sub['id']
                                if handle not in last_solved_ids:
                                    last_solved_ids[handle] = s_id
                                    break
                                if s_id > last_solved_ids[handle]:
                                    prob = sub['problem']
                                    msg = (f"🔥 <b>{handle}</b> решил задачу!\n"
                                           f"📝 {prob['name']}\n"
                                           f"🔗 https://codeforces.com/contest/{prob['contestId']}/problem/{prob['index']}")
                                    await bot.send_message(MY_CHAT_ID, msg, parse_mode="HTML")
                                    last_solved_ids[handle] = s_id
                except Exception as e:
                    print(f"Ошибка проверки Codeforces: {e}", flush=True)
                await asyncio.sleep(2)
            await asyncio.sleep(60)

async def main():
    await start_webserver()
    print("✅ Веб-сервер запущен", flush=True)
    
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Старые сообщения сброшены", flush=True)
    
    asyncio.create_task(check_updates())
    print("✅ Шпион начал работу. Бот ждет сообщений...", flush=True)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web
from datetime import datetime

# --- НАСТРОЙКИ ---
TOKEN = '8653073291:AAG7ztIMZfgzvfJPr_vXQy5qhvywMWbHbvM'
MY_CHAT_ID = 7951275068
WATCH_LIST = ['Alihan_7', 'NullPhase', 'whyy', 'matanov']

bot = Bot(token=TOKEN)
dp = Dispatcher()
last_solved_ids = {}

# --- КОСТЫЛЬ ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()

# --- ОБРАБОТЧИКИ КОМАНД ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🕵️‍♂️ Бот-шпион запущен!\nЯ слежу за Codeforces и пришлю уведомление, как только кто-то из списка решит задачу.")

@dp.message(Command("check"))
async def cmd_check(message: types.Message):
    targets = ", ".join(WATCH_LIST)
    await message.answer(f"✅ Я работаю!\nСлежу за: <code>{targets}</code>", parse_mode="HTML")

# --- ЛОГИКА ШПИОНА ---
async def check_updates():
    async with aiohttp.ClientSession() as session:
        while True:
            for handle in WATCH_LIST:
                try:
                    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=5"
                    async with session.get(url) as resp:
                        data = await resp.json()
                    if data.get('status') == 'OK':
                        for sub in data['result']:
                            if sub['verdict'] == 'OK':
                                s_id = sub['id']
                                if handle not in last_solved_ids:
                                    last_solved_ids[handle] = s_id
                                    break
                                if s_id > last_solved_ids[handle]:
                                    prob = sub['problem']
                                    msg = (f"🔥 <b>{handle}</b> решил задачу!\n"
                                           f"📝 {prob['name']} (Рейтинг: {prob.get('rating', '?')})\n"
                                           f"🔗 https://codeforces.com/contest/{prob['contestId']}/problem/{prob['index']}")
                                    await bot.send_message(MY_CHAT_ID, msg, parse_mode="HTML")
                                    last_solved_ids[handle] = s_id
                except: pass
                await asyncio.sleep(2)
            await asyncio.sleep(60)

async def main():
    await start_webserver()
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(check_updates())
    print("Бот официально запущен в облаке!")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())

