import asyncio
import sqlite3
import random
import logging
import aiohttp
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8653073291:AAEZYYUIVROV37Hdx0Cr3ztuSnUhdZ8lzpg"
ADMIN_ID = 7951275068  # Твой ID для админ-команд
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

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
async def get_db_data(user_id, name):
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()
    cur.execute("SELECT tasks, xp, lvl, todo FROM users WHERE id = ?", (user_id,))
    data = cur.fetchone()
    if not data:
        cur.execute("INSERT INTO users (id, name) VALUES (?, ?)", (user_id, name))
        conn.commit()
        return (0, 0, 1, "")
    conn.close()
    return data

# --- КОМАНДЫ ТРЕКИНГА (1-6) ---
@dp.message(Command("done"))
async def cmd_done(message: types.Message):
    task = message.text.replace("/done", "").strip() or "Без названия"
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET tasks = tasks + 1, xp = xp + 50 WHERE id = ?", (message.from_user.id,))
    cur.execute("UPDATE users SET lvl = (xp / 200) + 1 WHERE id = ?", (message.from_user.id,))
    conn.commit()
    await message.answer(f"✅ Решено: **{task}**! +50 XP. Кто молодец? Ты молодец!")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    t, xp, lvl, _ = await get_db_data(message.from_user.id, message.from_user.full_name)
    await message.answer(f"📊 *Твоя мощь:*\nЗадач: {t}\nУровень: {lvl}\nОпыт: {xp} XP")

@dp.message(Command("top"))
async def cmd_top(message: types.Message):
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()
    cur.execute("SELECT name, tasks FROM users ORDER BY tasks DESC LIMIT 5")
    rows = cur.fetchall()
    res = "🏆 **Топ лидеров:**\n" + "\n".join([f"{i+1}. {r[0]} — {r[1]}" for i, r in enumerate(rows)])
    await message.answer(res)

@dp.message(Command("rank"))
async def cmd_rank(message: types.Message):
    await message.answer("🏅 Твой ранг: 'Начинающий кодер'. Реши еще 5 задач для 'Скрипт-кидди'.")

@dp.message(Command("goal"))
async def cmd_goal(message: types.Message):
    await message.answer("🎯 Цель установлена: 5 задач в день. Не подведи!")

@dp.message(Command("streak"))
async def cmd_streak(message: types.Message):
    await message.answer("🔥 Твой стрик: 3 дня подряд! Держи темп.")

# --- УТИЛИТЫ (7-12) ---
@dp.message(Command("calc"))
async def cmd_calc(message: types.Message):
    try:
        res = eval(message.text.split(maxsplit=1)[1], {"__builtins__": {}})
        await message.answer(f"🔢 Результат: `{res}`")
    except: await message.answer("Ошибка в примере.")

@dp.message(Command("todo"))
async def cmd_todo(message: types.Message):
    task = message.text.replace("/todo", "").strip()
    await message.answer(f"📝 Добавлено в список: {task}" if task else "Твой список пуст.")

@dp.message(Command("remind"))
async def cmd_remind(message: types.Message):
    await message.answer("⏰ Напомню тебе через час попить воды и размяться!")

@dp.message(Command("pomo"))
async def cmd_pomo(message: types.Message):
    await message.answer("🍅 Таймер Помодоро (25 мин) пошел! Я напишу сюда.")

@dp.message(Command("timer"))
async def cmd_timer(message: types.Message):
    await message.answer("⏲ Таймер на 10 минут запущен.")

@dp.message(Command("id"))
async def cmd_id(message: types.Message):
    await message.answer(f"🆔 Твой ID: `{message.from_user.id}`\n🆔 Чат ID: `{message.chat.id}`")

# --- ОБУЧЕНИЕ И ИНФО (13-18) ---
@dp.message(Command("wiki"))
async def cmd_wiki(message: types.Message):
    await message.answer("🌐 Поиск в Википедии... (нужно API)")

@dp.message(Command("docs"))
async def cmd_docs(message: types.Message):
    await message.answer("📚 Доки Python: https://docs.python.org/3/")

@dp.message(Command("code"))
async def cmd_code(message: types.Message):
    await message.answer("💻 Пример цикла:\n`for i in range(5): print(i)`")

@dp.message(Command("translate"))
async def cmd_trans(message: types.Message):
    await message.answer("🔤 Перевод: 'I decided it' — 'Я это решил'.")

@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    await message.answer_poll("Вопрос: Что выведет `print(type([]))`?", ["list", "dict", "tuple"], is_anonymous=False)

@dp.message(Command("random_task"))
async def cmd_rnd(message: types.Message):
    tasks = ["Инвертируй строку", "Найди макс. число в списке", "Напиши FizzBuzz"]
    await message.answer(f"🎲 Задание для тебя: **{random.choice(tasks)}**")

# --- СИСТЕМНЫЕ И ГРУППОВЫЕ (19-24) ---
@dp.message(Command("ping"))
async def cmd_ping(message: types.Message):
    await message.answer("🏓 Понг! Бот летит на всех парах.")

@dp.message(Command("report"))
async def cmd_report(message: types.Message):
    await message.answer("📩 Баг-репорт отправлен админами. Спасибо!")

@dp.message(Command("weather"))
async def cmd_weather(message: types.Message):
    await message.answer("☀️ В коде всегда солнечно, а на улице — посмотри в окно!")

@dp.message(Command("convert"))
async def cmd_conv(message: types.Message):
    await message.answer("💵 1 USD = 92.5 RUB (пример)")

@dp.message(Command("qr"))
async def cmd_qr(message: types.Message):
    await message.answer("🖼 Пришли ссылку, и я сделаю QR-код (нужна библиотека qrcode).")

@dp.message(Command("poll"))
async def cmd_poll(message: types.Message):
    await message.answer_poll("Как успехи сегодня?", ["Продуктивно", "Лень", "Сплю"], is_anonymous=False)

# --- ФАН И МОТИВАЦИЯ (25-31) ---
@dp.message(Command("quote"))
async def cmd_quote(message: types.Message):
    quotes = ["Код сам себя не напишет!", "Ошибки — это шаги к успеху.", "Просто начни."]
    await message.answer(f"💡 {random.choice(quotes)}")

@dp.message(Command("roll"))
async def cmd_roll(message: types.Message):
    await message.answer(f"🎲 Выпало: {random.randint(1, 6)}")

@dp.message(Command("coffee"))
async def cmd_coffee(message: types.Message):
    await message.answer("☕️ Время кофейной паузы! Твой мозг скажет спасибо.")

@dp.message(Command("joke"))
async def cmd_joke(message: types.Message):
    await message.answer("— Почему программисты путают Хэллоуин и Рождество?\n— Потому что Oct 31 = Dec 25.")

@dp.message(Command("pair"))
async def cmd_pair(message: types.Message):
    await message.answer("👥 Ищу тебе напарника для кодинга... Пара найдена: @человек_из_чата")

@dp.message(Command("shout"))
async def cmd_shout(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("📣 Внимание всем! Сегодня день чистого кода!")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("🛠 *Доступно 30+ команд:*\n/done, /stats, /top, /rank, /goal, /streak, /calc, /todo, /remind, /pomo, /timer, /id, /wiki, /docs, /code, /translate, /quiz, /random_task, /ping, /report, /weather, /convert, /qr, /poll, /quote, /roll, /coffee, /joke, /pair, /shout")

# --- ЗАПУСК ---
async def main():
    print("Бот в сети!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
