import asyncio
import aiohttp
from aiogram import Bot, Dispatcher
from aiohttp import web
from datetime import datetime

# --- НАСТРОЙКИ ---
TOKEN = '8653073291:AAHAszBr4peH4c4A_QpxqboW4UwN_UXZF4g'
MY_CHAT_ID = 7951275068
WATCH_LIST = ['Alihan_7', 'NullPhase', 'whyy', 'matanov']

bot = Bot(token=TOKEN)
dp = Dispatcher()
last_solved_ids = {}

# --- КОСТЫЛЬ ДЛЯ RENDER (ВЕБ-СЕРВЕР) ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000) # Render ищет порт здесь
    await site.start()

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
    # 1. Запускаем сервер для Render
    await start_webserver()
    
    # 2. ЖЕСТКИЙ СБРОС (выгоняем призрака)
    print("Принудительный сброс сессий...")
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.sleep(2) # Даем Telegram время «выдохнуть»
    
    # 3. Запускаем слежку
    asyncio.create_task(check_updates())
    
    # 4. Запускаем бота
    print("Бот-шпион в облаке запущен!")
    await dp.start_polling(bot, skip_updates=True) # skip_updates пропустит старый спам
if __name__ == "__main__":
    asyncio.run(main())

