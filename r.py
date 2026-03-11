import asyncio
import aiohttp
import sqlite3
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode

# ---------------- CONFIG ----------------
TOKEN = "8653073291:AAG6jr04iA3i6-_3VXsHjSgXoipZtSC88fM"   # сюда вставь токен бота
OWNER_HANDLE = "whyy"      # твой ник в Codeforces
OWNER_ID = 7951275068       # твой Telegram ID
CHECK_INTERVAL = 30         # секунда между проверками
# ---------------------------------------

bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# ---------------- DATABASE ----------------
db = sqlite3.connect("cf.db")
cur = db.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS handles(
    handle TEXT PRIMARY KEY,
    last INTEGER
)
""")
db.commit()

# ---------------- HELPERS ----------------
def allowed(message: types.Message):
    return message.from_user.id == OWNER_ID

async def get_user_status(handle):
    url = f"https://codeforces.com/api/user.status?handle={handle}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
    return data

async def get_solved(handle):
    data = await get_user_status(handle)
    if data["status"] != "OK":
        return 0
    return sum(1 for s in data["result"] if s.get("verdict") == "OK")

# ---------------- COMMANDS ----------------
@dp.message(Command("start"))
async def start(message: types.Message):
    if not allowed(message):
        return
    text = """
<b>CF Tracker Bot</b>
/add handle - добавить handle
/remove handle - удалить handle
/list - список handle
/rating <handle> - рейтинг
/last <handle> - последние решения
/top - топ по решённым задачам
/motivate - мотивация
/funny - шутка
/random - случайная задача
/stats <handle> - статистика
/help - список команд
"""
    await message.answer(text)

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await start(message)

@dp.message(Command("add"))
async def add(message: types.Message):
    if not allowed(message):
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Используй: /add handle")
        return
    handle = args[1]
    cur.execute("INSERT OR IGNORE INTO handles VALUES(?,0)", (handle,))
    db.commit()
    await message.answer(f"✅ Добавлен handle {handle}")

@dp.message(Command("remove"))
async def remove(message: types.Message):
    if not allowed(message):
        return
    args = message.text.split()
    if len(args) < 2:
        return
    handle = args[1]
    cur.execute("DELETE FROM handles WHERE handle=?", (handle,))
    db.commit()
    await message.answer(f"❌ Удален handle {handle}")

@dp.message(Command("list"))
async def list_handles(message: types.Message):
    if not allowed(message):
        return
    cur.execute("SELECT handle FROM handles")
    rows = cur.fetchall()
    if not rows:
        await message.answer("Список пуст")
        return
    await message.answer("\n".join(r[0] for r in rows))

@dp.message(Command("rating"))
async def rating(message: types.Message):
    if not allowed(message):
        return
    args = message.text.split()
    if len(args) < 2:
        return
    handle = args[1]
    url = f"https://codeforces.com/api/user.info?handles={handle}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
    if data["status"] != "OK":
        await message.answer("Ошибка API")
        return
    user = data["result"][0]
    text = f"<b>{handle}</b>\nРейтинг: {user.get('rating','unrated')}\nМакс: {user.get('maxRating','unrated')}\nРанг: {user.get('rank','')}"
    await message.answer(text)

@dp.message(Command("last"))
async def last(message: types.Message):
    if not allowed(message):
        return
    args = message.text.split()
    if len(args) < 2:
        return
    handle = args[1]
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=5"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
    text = ""
    for s in data["result"]:
        problem = s["problem"]["name"]
        verdict = s.get("verdict", "")
        text += f"{problem} — {verdict}\n"
    await message.answer(text)

@dp.message(Command("motivate"))
async def motivate(message: types.Message):
    if not allowed(message):
        return
    phrases = [
        "Ты крутой! 💪", "Давай ещё!", "Решай задачи как турист!", "🔥 Вперёд к новым победам!"
    ]
    await message.answer(random.choice(phrases))

@dp.message(Command("funny"))
async def funny(message: types.Message):
    if not allowed(message):
        return
    jokes = [
        "Почему программисты не любят природу? Слишком много багов! 😂",
        "WA - это не ошибка, это испытание 💀",
        "TLE? Просто Codeforces проверяет твоё терпение ⏳",
        "Решил задачу? А тесты проходят? 😅"
    ]
    await message.answer(random.choice(jokes))

@dp.message(Command("random"))
async def random_problem(message: types.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://codeforces.com/api/problemset.problems") as resp:
            data = await resp.json()
    problems = data["result"]["problems"]
    problem = random.choice(problems)
    url = f"https://codeforces.com/problemset/problem/{problem['contestId']}/{problem['index']}"
    await message.answer(f"{problem['name']} ({problem.get('rating','?')} rating)\n{url}")

@dp.message(Command("top"))
async def top(message: types.Message):
    if not allowed(message):
        return
    cur.execute("SELECT handle FROM handles")
    handles = [r[0] for r in cur.fetchall()]
    scores = []
    for h in handles:
        solved = await get_solved(h)
        scores.append((h, solved))
    scores.sort(key=lambda x: x[1], reverse=True)
    text = "🏆 Топ пользователей по решённым задачам:\n"
    for i, (h, s) in enumerate(scores[:5], 1):
        text += f"{i}. {h} — {s} задач\n"
    await message.answer(text)

# ------------------ TRACKER ------------------
async def tracker():
    while True:
        cur.execute("SELECT handle,last FROM handles")
        rows = cur.fetchall()
        async with aiohttp.ClientSession() as session:
            for handle, last_id in rows:
                try:
                    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=1"
                    async with session.get(url) as resp:
                        data = await resp.json()
                    sub = data["result"][0]
                    sid = sub["id"]
                    if last_id == 0:
                        cur.execute("UPDATE handles SET last=? WHERE handle=?", (sid, handle))
                        db.commit()
                        continue
                    if sid != last_id:
                        cur.execute("UPDATE handles SET last=? WHERE handle=?", (sid, handle))
                        db.commit()
                        problem = sub["problem"]["name"]
                        # уведомления
                        if handle == OWNER_HANDLE:
                            texts = [
                                f"🎉 Еее! Ты решил {problem}! 💪🔥",
                                f"🥳 Отлично, {problem} решена!",
                                f"💥 Прям как турист! {problem} done!"
                            ]
                        else:
                            texts = [
                                f"🤔 О нет! {handle} решил {problem}. Нужно подтянуться! ⚡",
                                f"😅 {handle} справился с {problem}. Давай быстрее!",
                                f"⚡ {handle} решил {problem}. Пора действовать!"
                            ]
                        await bot.send_message(OWNER_ID, random.choice(texts))
                except Exception as e:
                    print(e)
        await asyncio.sleep(CHECK_INTERVAL)

# ------------------ MAIN ------------------
async def post_init(application):
    asyncio.create_task(tracker())

def main():
    from telegram.ext import ApplicationBuilder, CommandHandler
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("list", list_handles))
    app.add_handler(CommandHandler("rating", rating))
    app.add_handler(CommandHandler("last", last))
    app.add_handler(CommandHandler("motivate", motivate))
    app.add_handler(CommandHandler("funny", funny))
    app.add_handler(CommandHandler("random", random_problem))
    app.add_handler(CommandHandler("top", top))

    app.run_polling()

if __name__ == "__main__":
    main()
