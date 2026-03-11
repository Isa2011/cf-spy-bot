import asyncio
import logging
import json
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from collections import Counter

# --- НАСТРОЙКИ ---
API_TOKEN = 'ВАШ_ТОКЕН_ТЕЛЕГРАМ'
ADMIN_ID = 12345678  # Твой ID, чтобы бот знал, кому слать отчеты
DB_FILE = "friends.json"

# Загрузка данных
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

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
async def fetch_cf(method, params):
    async with aiohttp.ClientSession() as session:
        url = f"https://codeforces.com/api/{method}"
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            return data.get("result") if data.get("status") == "OK" else None

# --- КОМАНДЫ ---

@dp.message(Command("cf_follow"))
async def cmd_follow(message: types.Message, command: CommandObject):
    if not command.args: return await message.answer("Пиши: `/cf_follow handle`")
    handle = command.args.strip()
    FRIENDS.add(handle)
    save_friends()
    await message.answer(f"✅ Подписался на **{handle}**")

@dp.message(Command("ignore"))
async def cmd_ignore(message: types.Message, command: CommandObject):
    handle = command.args
    if handle in FRIENDS:
        FRIENDS.remove(handle)
        save_friends()
        await message.answer(f"❌ Отписался от {handle}")
    else:
        await message.answer("Его и так нет в списке.")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message, command: CommandObject):
    handle = command.args or "твой_ник_по_умолчанию"
    res = await fetch_cf("user.info", {"handles": handle})
    if res:
        u = res[0]
        msg = (f"📊 **{u['handle']}** ({u.get('rank', 'N/A')})\n"
               f"⭐ Рейтинг: {u.get('rating', 0)} (max: {u.get('maxRating', 0)})\n"
               f"🏢 Организация: {u.get('organization', 'Нет')}")
        await message.answer(msg, parse_mode="Markdown")

@dp.message(Command("weak"))
async def cmd_weak(message: types.Message, command: CommandObject):
    handle = command.args or "твой_ник"
    await message.answer(f"🔎 Анализирую последние ошибки {handle}...")
    status = await fetch_cf("user.status", {"handle": handle, "from": 1, "count": 100})
    
    if status:
        failed_tags = []
        for sub in status:
            if sub['verdict'] != 'OK':
                failed_tags.extend(sub['problem'].get('tags', []))
        
        most_common = Counter(failed_tags).most_common(5)
        report = "\n".join([f"• {tag}: {count} ошибок" for tag, count in most_common])
        await message.answer(f"📉 **Твои слабые темы:**\n{report}\n\nПорешай задачи на эти теги!")

@dp.message(Command("compare"))
async def cmd_compare(message: types.Message, command: CommandObject):
    if not command.args: return await message.answer("Пиши: `/compare handle`")
    me = "твой_ник"
    friend = command.args.strip()
    
    res = await fetch_cf("user.info", {"handles": f"{me};{friend}"})
    if res and len(res) == 2:
        m, f = res[0], res[1]
        diff = m.get('rating', 0) - f.get('rating', 0)
        sign = "🟢 ты впереди на" if diff >= 0 else "🔴 ты отстаешь на"
        await message.answer(f"🆚 **{me} vs {friend}**\n"
                             f"Ты: {m.get('rating', 0)}\n"
                             f"Друг: {f.get('rating', 0)}\n"
                             f"Разница: {abs(diff)} ({sign})")

# --- ФОНОВАЯ ПРОВЕРКА (Упрощенно) ---
async def checker():
    while True:
        for handle in list(FRIENDS):
            res = await fetch_cf("user.status", {"handle": handle, "from": 1, "count": 2})
            if res and res[0]['verdict'] == 'OK':
                sub = res[0]
                if last_solved_ids.get(handle) != sub['id']:
                    last_solved_ids[handle] = sub['id']
                    # Отправка уведомления ADMIN_ID
                    await bot.send_message(ADMIN_ID, f"🔥 {handle} решил: {sub['problem']['name']}")
        await asyncio.sleep(60)

async def main():
    asyncio.create_task(checker())
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
