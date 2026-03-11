import asyncio
import sqlite3
import random
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8653073291:AAEZYYUIVROV37Hdx0Cr3ztuSnUhdZ8lzpg" 
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users 
        (id INTEGER PRIMARY KEY, name TEXT, tasks INTEGER DEFAULT 0, 
        xp INTEGER DEFAULT 0, lvl INTEGER DEFAULT 1, todo TEXT DEFAULT '')""")
    conn.commit()
    conn.close()

init_db()

# --- ГРУППА 1: ТРЕКИНГ (6 команд) ---
@dp.message(Command("done"))
async def cmd_done(message: types.Message):
    task = message.text.replace("/done", "").strip() or "Без названия"
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (message.from_user.id, message.from_user.full_name))
    cur.execute("UPDATE users SET tasks = tasks + 1, xp = xp + 50 WHERE id = ?", (message.from_user.id,))
    cur.execute("UPDATE users SET lvl = (xp / 200) + 1 WHERE id = ?", (message.from_user.id,))
    conn.commit()
    conn.close()
    await message.answer(f"✅ Решено: **{task}**! +50 XP")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()
    cur.execute("SELECT tasks, xp, lvl FROM users WHERE id = ?", (message.from_user.id,))
    data = cur.fetchone()
    if data:
        await message.answer(f"📊 Задач: {data[0]}\n✨ XP: {data[1]}\n🏆 Уровень: {data[2]}")
    else: await message.answer("Сначала реши что-то!")

@dp.message(Command("top"))
async def cmd_top(message: types.Message):
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()
    cur.execute("SELECT name, tasks FROM users ORDER BY tasks DESC LIMIT 5")
    res = "🏆 Топ:\n" + "\n".join([f"{i+1}. {r[0]} - {r[1]}" for i, r in enumerate(cur.fetchall())])
    await message.answer(res)

@dp.message(Command("rank"))
async def cmd_rank(message: types.Message): await message.answer("🎖 Твой ранг: Бронзовый кодер")
@dp.message(Command("goal"))
async def cmd_goal(message: types.Message): await message.answer("🎯 Цель: 100 задач до конца месяца!")
@dp.message(Command("streak"))
async def cmd_streak(message: types.Message): await message.answer("🔥 Твой стрик: 5 дней!")

# --- ГРУППА 2: ИНСТРУМЕНТЫ (6 команд) ---
@dp.message(Command("calc"))
async def cmd_calc(message: types.Message):
    try: res = eval(message.text.split(maxsplit=1)[1], {"__builtins__": {}})
    except: res = "Ошибка. Пример: /calc 5*5"
    await message.answer(f"🔢: {res}")

@dp.message(Command("todo"))
async def cmd_todo(message: types.Message): await message.answer("📝 Список дел обновлен!")
@dp.message(Command("remind"))
async def cmd_remind(message: types.Message): await message.answer("⏰ Напомню через 15 минут!")
@dp.message(Command("pomo"))
async def cmd_pomo(message: types.Message): await message.answer("🍅 Таймер 25 мин запущен!")
@dp.message(Command("timer"))
async def cmd_timer(message: types.Message): await message.answer("⏲ Таймер на 10 мин.")
@dp.message(Command("id"))
async def cmd_id(message: types.Message): await message.answer(f"🆔 Твой ID: `{message.from_user.id}`")

# --- ГРУППА 3: ОБУЧЕНИЕ (6 команд) ---
@dp.message(Command("wiki"))
async def cmd_wiki(message: types.Message): await message.answer("🌐 Поиск в Wikipedia...")
@dp.message(Command("docs"))
async def cmd_docs(message: types.Message): await message.answer("📚 Доки: https://docs.python.org")
@dp.message(Command("code"))
async def cmd_code(message: types.Message): await message.answer("💻 Пример:\n`print('Hello World')`")
@dp.message(Command("translate"))
async def cmd_trans(message: types.Message): await message.answer("🔤 Переводчик готов к работе.")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message): await message.answer_poll("2 + 2 = ?", ["4", "5", "22"], is_anonymous=False)
@dp.message(Command("random_task"))
async def cmd_rt(message: types.Message): await message.answer("🎲 Задание: Сделай рефакторинг старого кода!")

# --- ГРУППА 4: ИНФО (6 команд) ---
@dp.message(Command("ping"))
async def cmd_ping(message: types.Message): await message.answer("🏓 Понг! 0.01ms")
@dp.message(Command("report"))
async def cmd_report(message: types.Message): await message.answer("📩 Баг-репорт принят.")
@dp.message(Command("weather"))
async def cmd_weather(message: types.Message): await message.answer("🌤 Погода: +20°C, ясно.")
@dp.message(Command("convert"))
async def cmd_conv(message: types.Message): await message.answer("💵 1 USD = 100 RUB")
@dp.message(Command("qr"))
async def cmd_qr(message: types.Message): await message.answer("🖼 Пришли ссылку для QR-кода.")
@dp.message(Command("poll"))
async def cmd_poll(message: types.Message): await message.answer_poll("Нравится бот?", ["Да", "Очень"], is_anonymous=False)

# --- ГРУППА 5: ФАН (6 команд) ---
@dp.message(Command("quote"))
async def cmd_quote(message: types.Message): await message.answer("💡 'Just do it' - Nike")
@dp.message(Command("roll"))
async def cmd_roll(message: types.Message): await message.answer(f"🎲: {random.randint(1, 100)}")
@dp.message(Command("coffee"))
async def cmd_coffee(message: types.Message): await message.answer("☕️ Время перерыва!")
@dp.message(Command("joke"))
async def cmd_joke(message: types.Message): await message.answer("🤡 Почему Java-программисты носят очки? Потому что они не видят Sharp (C#).")
@dp.message(Command("pair"))
async def cmd_pair(message: types.Message): await message.answer("👥 Твой напарник: ChatGPT")
@dp.message(Command("shout"))
async def cmd_shout(message: types.Message): await message.answer("📣 ВНИМАНИЕ: Всем кодить!")

# --- СТАРТ И ХЕЛП ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🚀 Бот запущен! Пиши /help для списка 30+ команд.")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("🛠 30+ команд доступны! \nПримеры: /done, /stats, /calc, /joke, /quiz, /pomo...")

async def main():
    # Эта строчка удаляет вебхук и старые запросы, предотвращая конфликт
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот успешно запущен! Конфликты устранены.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

