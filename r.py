import asyncio
import logging
import json
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from aiogram.types import BotCommand
from collections import Counter

# --- НАСТРОЙКИ ---
# Вставь сюда свой токен без пробелов
API_TOKEN = '8653073291:AAEZYYUIVROV37Hdx0Cr3ztuSnUhdZ8lzpg' 
# Вставь сюда СВОЙ числовой ID (узнай в @userinfobot)
ADMIN_ID = 7951275068  

DB_FILE = "friends.json"

def load_friends():
    try:
        with open(DB_FILE, "r") as f: return set(json.load(f))
    except: return set()

def save_friends():
    with open(DB_FILE, "w") as f: json.dump(list(FRIENDS), f)

FRIENDS = load_friends()
last_solved_ids = {}

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

async def fetch_cf(method, params):
    async with aiohttp.ClientSession() as session:
        url = f"https://codeforces.com/api/{method}"
        try:
            async with session.get(url, params=params, timeout=15) as resp:
                data = await resp.json()
                if data.get("status") == "OK":
                    return data.get("result")
                return None
        except Exception as e:
            logging.error(f"CF API Error: {e}")
            return None

# --- КОМАНДЫ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🚀 **CF Watcher AI запущен!**\n\n"
        "Я буду следить за твоими друзьями и подсказывать, где твои слабые места.\n"
        "Жми кнопку 'Меню', чтобы увидеть все команды."
    )

@dp.message(Command("cf_follow"))
async def cmd_follow(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("⚠️ Пиши: `/cf_follow ник_друга`", parse_mode="Markdown")
    handle = command.args.strip()
    FRIENDS.add(handle)
    save_friends()
    await message.answer(f"✅ Добавил **{handle}** в список. Теперь я не спущу с него глаз!", parse_mode="Markdown")

@dp.message(Command("weak"))
async def cmd_weak(message: types.Message, command: CommandObject):
    handle = command.args.strip() if command.args else "tourist" # Поставь свой ник
    await message.answer(f"🧪 Анализирую последние 100 посылок {handle}...")
    res = await fetch_cf("user.status", {"handle": handle, "from": 1, "count": 100})
    if res:
        # Считаем только теги задач, которые НЕ были решены (вердикт не OK)
        wrong_tags = [tag for sub in res if sub['verdict'] != 'OK' for tag in sub['problem'].get('tags', [])]
        if not wrong_tags:
            return await message.answer("💪 Ошибок нет. Либо ты гений, либо мало решаешь!")
        
        top = Counter(wrong_tags).most_common(5)
        text = "\n".join([f"❌ **{tag}**: {count} провалов" for tag, count in top])
        await message.answer(f"⚠️ **Твои зоны роста (Weak Topics):**\n\n{text}", parse_mode="Markdown")

@dp.message(Command("compare"))
async def cmd_compare(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("Пиши: `/compare ник_друга`")
    
    # Сравниваем tourist (как пример) и твоего друга
    handles = f"tourist;{command.args.strip()}"
    res = await fetch_cf("user.info", {"handles": handles})
    if res and len(res) == 2:
        u1, u2 = res[0], res[1]
        msg = (f"⚔️ **Битва рейтингов:**\n\n"
               f"👤 {u1['handle']}: {u1.get('rating', 0)} ({u1.get('rank', 'N/A')})\n"
               f"👤 {u2['handle']}: {u2.get('rating', 0)} ({u2.get('rank', 'N/A')})\n\n"
               f"📈 Разница: {abs(u1.get('rating', 0) - u2.get('rating', 0))}")
        await message.answer(msg)

# --- ФОНОВАЯ ПРОВЕРКА ---
async def checker():
    while True:
        if not FRIENDS or ADMIN_ID == 0:
            await asyncio.sleep(20)
            continue
            
        for handle in list(FRIENDS):
            res = await fetch_cf("user.status", {"handle": handle, "from": 1, "count": 5})
            if res:
                for sub in res:
                    if sub['verdict'] == 'OK':
                        s_id = sub['id']
                        if handle not in last_solved_ids:
                            last_solved_ids[handle] = s_id
                        elif last_solved_ids[handle] != s_id:
                            last_solved_ids[handle] = s_id
                            prob = sub['problem']
                            text = (f"🔔 **{handle}** только что закрыл задачу!\n\n"
                                    f"📓 {prob['name']}\n"
                                    f"📊 Рейтинг: {prob.get('rating', '???')}\n"
                                    f"🏷 Теги: {', '.join(prob.get('tags', []))}\n"
                                    f"🔗 [Решение](https://codeforces.com/contest/{sub.get('contestId')}/problem/{prob['index']})")
                            try:
                                await bot.send_message(ADMIN_ID, text, parse_mode="Markdown", disable_web_page_preview=True)
                            except Exception as e:
                                logging.error(f"Send error: {e}")
                        break
            await asyncio.sleep(2) # Маленькая пауза между запросами к разным людям
        await asyncio.sleep(60)

async def main():
    # Настройка команд
    commands = [
        BotCommand(command="start", description="Инфо о боте"),
        BotCommand(command="cf_follow", description="Добавить друга для слежки"),
        BotCommand(command="weak", description="Твои слабые темы"),
        BotCommand(command="compare", description="Сравнить с другом"),
        BotCommand(command="list", description="Кто в списке?")
    ]
    await bot.set_my_commands(commands)
    
    asyncio.create_task(checker())
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")

