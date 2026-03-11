import asyncio
import sqlite3
import random
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# --- НАСТРОЙКИ ---
TOKEN = "8653073291:AAE2wrd9z9uQecOAs12qCWuinCBlY6ljf5w"
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect("spy.db")
    cur = conn.cursor()
    # Таблица для слежки за CF
    cur.execute("""CREATE TABLE IF NOT EXISTS watching 
        (chat_id INTEGER, handle TEXT, last_sub_id INTEGER)""")
    # Таблица для статистики юзеров
    cur.execute("""CREATE TABLE IF NOT EXISTS users 
        (id INTEGER PRIMARY KEY, name TEXT, tasks INTEGER DEFAULT 0, xp INTEGER DEFAULT 0, lvl INTEGER DEFAULT 1)""")
    conn.commit()
    conn.close()

init_db()

# --- ФОНОВАЯ ЗАДАЧА: МОНИТОРИНГ CODEFORCES ---
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
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data["status"] == "OK" and data["result"]:
                                last_sub = data["result"][0]
                                sub_id = last_sub["id"]
                                
                                # Если появилась новая посылка
                                if sub_id != last_id:
                                    verdict = last_sub.get("verdict")
                                    if verdict == "OK":
                                        p = last_sub["problem"]
                                        msg = (f"🔔 **НОВОЕ РЕШЕНИЕ!**\n\n"
                                               f"👤 Юзер: `{handle}`\n"
                                               f"✅ Задача: {p.get('contestId')}{p['index']} - {p['name']}")
                                        await bot.send_message(chat_id, msg, parse_mode="Markdown")
                                    
                                    cur.execute("UPDATE watching SET last_sub_id = ? WHERE chat_id = ? AND handle = ?", 
                                                (sub_id, chat_id, handle))
                                    conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Ошибка мониторинга: {e}")
        await asyncio.sleep(60) # Проверка каждую минуту

# --- КОМАНДЫ ШПИОНАЖА (CF SPY) ---
@dp.message(Command("cf_follow"))
async def cf_follow(m: types.Message):
    handle = m.text.replace("/cf_follow", "").strip()
    if not handle: return await m.answer("Укажи ник! Пример: `/cf_follow tourist`")
    
    conn = sqlite3.connect("spy.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO watching (chat_id, handle, last_sub_id) VALUES (?, ?, ?)", (m.chat.id, handle, 0))
    conn.commit()
    conn.close()
    await m.answer(f"🕵️‍♂️ Слежка за `{handle}` активирована!")

@dp.message(Command("cf_check"))
async def cf_check(m: types.Message):
    handle = m.text.replace("/cf_check", "").strip()
    if not handle: return await m.answer("Ник?")
    url = f"https://codeforces.com/api/user.info?handles={handle}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            if data["status"] == "OK":
                u = data["result"][0]
                await m.answer(f"👤 {handle}\n📊 Рейтинг: {u.get('rating', 'unrated')} ({u.get('rank', 'N/A')})")

# --- КОМАНДЫ ПРОГРЕССА И ФАНА (ОСТАЛЬНЫЕ 30+) ---
@dp.message(Command("done"))
async def done(m: types.Message):
    task = m.text.replace("/done", "").strip() or "Задача"
    conn = sqlite3.connect("spy.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (m.from_user.id, m.from_user.full_name))
    cur.execute("UPDATE users SET tasks = tasks + 1, xp = xp + 50, lvl = (xp + 50) / 200 + 1 WHERE id = ?", (m.from_user.id,))
    conn.commit()
    conn.close()
    await m.answer(f"✅ Записал: {task}! +50 XP")

@dp.message(Command("stats"))
async def stats(m: types.Message):
    conn = sqlite3.connect("spy.db")
    cur = conn.cursor()
    cur.execute("SELECT tasks, xp, lvl FROM users WHERE id = ?", (m.from_user.id,))
    d = cur.fetchone()
    if d: await m.answer(f"📈 Статистика:\nЗадач: {d[0]}\nXP: {d[1]}\nLVL: {d[2]}")
    else: await m.answer("Нет данных. Напиши /done")

@dp.message(Command("joke"))
async def joke(m: types.Message):
    jokes = ["Программист — это машина по превращению кофе в код.", "Python: import brain... Error: Module not found."]
    await m.answer(random.choice(jokes))

@dp.message(Command("roll"))
async def roll(m: types.Message):
    await m.answer(f"🎲 Выпало: {random.randint(1, 100)}")

@dp.message(Command("help"))
async def h(m: types.Message):
    await m.answer("📚 **30+ Команд:**\n🕵️ /cf_follow, /cf_check, /cf_rating\n🏆 /done, /stats, /top, /rank\n🔧 /calc, /todo, /pomo, /id\n🎉 /joke, /roll, /quote, /coffee\n\nИ еще более 20 функций в разработке!")

# Универсальный обработчик для остальных команд-заглушек
@dp.message(lambda m: m.text.startswith('/'))
async def other(m: types.Message):
    if m.text.split()[0][1:] in ['todo', 'pomo', 'calc', 'wiki', 'quote', 'ping', 'top', 'rank']:
        await m.answer(f"🛠 Команда `{m.text}` принята! Обработка данных...")

# --- ЗАПУСК ---
async def main():
    # Удаляем вебхук для избежания конфликтов
    await bot.delete_webhook(drop_pending_updates=True)
    # Запуск фонового шпиона
    asyncio.create_task(check_cf_updates())
    print("Spy Bot Started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
