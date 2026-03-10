import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from datetime import datetime

# --- НАСТРОЙКИ ---
TOKEN = '8653073291:AAHAszBr4peH4c4A_QpxqboW4UwN_UXZF4g'
MY_CHAT_ID = 7951275068
WATCH_LIST = ['Alihan_7', 'NullPhase', 'whyy', 'matanov']

bot = Bot(token=TOKEN)
dp = Dispatcher()

# База данных последних решенных задач
last_solved_ids = {}

async def check_updates():
    """Фоновая проверка обновлений на Codeforces"""
    async with aiohttp.ClientSession() as session:
        while True:
            for handle in WATCH_LIST:
                try:
                    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=5"
                    async with session.get(url) as response:
                        if response.status != 200:
                            continue
                        data = await response.json()

                    if data.get('status') == 'OK':
                        for sub in data['result']:
                            if sub['verdict'] == 'OK':
                                sub_id = sub['id']
                                
                                if handle not in last_solved_ids:
                                    last_solved_ids[handle] = sub_id
                                    break
                                
                                if sub_id > last_solved_ids[handle]:
                                    prob = sub['problem']
                                    rating = prob.get('rating', '???')
                                    
                                    msg = (
                                        f"🔥 <b>{handle}</b> решил задачу!\n\n"
                                        f"📝 <b>Название:</b> {prob['name']}\n"
                                        f"📊 <b>Рейтинг:</b> {rating}\n"
                                        f"🔗 <a href='https://codeforces.com/contest/{prob['contestId']}/problem/{prob['index']}'>Открыть задачу</a>"
                                    )
                                    
                                    await bot.send_message(MY_CHAT_ID, msg, parse_mode="HTML")
                                    last_solved_ids[handle] = sub_id
                
                except Exception as e:
                    print(f"Ошибка проверки {handle}: {e}")
                
                await asyncio.sleep(2) # Пауза между запросами

            await asyncio.sleep(60) # Проверка списка раз в минуту

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Бот-шпион на aiogram запущен! Слежу за успехами на Codeforces... 🕵️‍♂️")

async def main():
    # Запускаем фоновую задачу
    asyncio.create_task(check_updates())
    # Запускаем бота
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")
