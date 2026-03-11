import asyncio
import random
import logging
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8771638954:AAG9mrksptIJKh-62ltsIVp-UF1E8GTqswA"
OWNER_ID = 7951275068
MY_HANDLE = "whyy"

CHECK_INTERVAL = 60

bot = Bot(TOKEN, parse_mode="HTML")
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

session = aiohttp.ClientSession()
last_submissions = {}

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎯 Предложи задачу")],
        [KeyboardButton(text="📊 Моя статистика")],
        [KeyboardButton(text="🏆 Топ друзей")],
        [KeyboardButton(text="📈 Рейтинг")]
    ],
    resize_keyboard=True
)

# ---------------- API ---------------- #

async def get_user_info(handle):
    url = f"https://codeforces.com/api/user.info?handles={handle}"
    async with session.get(url) as r:
        data = await r.json()
        return data["result"][0]

async def get_user_submissions(handle):
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=50"
    async with session.get(url) as r:
        data = await r.json()
        return data["result"]

async def get_problems():
    url = "https://codeforces.com/api/problemset.problems"
    async with session.get(url) as r:
        data = await r.json()
        return data["result"]

async def get_contests():
    url = "https://codeforces.com/api/contest.list"
    async with session.get(url) as r:
        data = await r.json()
        return data["result"]

async def get_friends():
    url = f"https://codeforces.com/api/user.friends?handle={MY_HANDLE}"
    async with session.get(url) as r:
        data = await r.json()
        return data["result"]  # список handle друзей

# ---------------- Мониторинг ---------------- #

async def monitor_friends():
    await bot.wait_until_ready()
    while True:
        try:
            friends = await get_friends()
            for handle in friends:
                subs = await get_user_submissions(handle)
                if not subs:
                    continue

                if handle not in last_submissions:
                    last_submissions[handle] = subs[0]["id"]
                    continue

                for s in subs:
                    if s["id"] == last_submissions[handle]:
                        break
                    if s["verdict"] == "OK":
                        p = s["problem"]
                        name = p["name"]
                        rating = p.get("rating", "?")
                        contest = p["contestId"]
                        index = p["index"]
                        link = f"https://codeforces.com/problemset/problem/{contest}/{index}"
                        msg = f"""
🏆 <b>Победа!</b>

👤 <b>{handle}</b> решил задачу

📌 <a href="{link}">{name}</a>
⭐ Рейтинг: <b>{rating}</b>

🔥 Отличная работа!
"""
                        await bot.send_message(OWNER_ID, msg)
                last_submissions[handle] = subs[0]["id"]
        except Exception as e:
            print(e)
        await asyncio.sleep(CHECK_INTERVAL)

# ---------------- Suggest ---------------- #

async def suggest_problem():
    user = await get_user_info(MY_HANDLE)
    rating = user.get("rating", 1200)
    data = await get_problems()
    problems = data["problems"]
    subs = await get_user_submissions(MY_HANDLE)
    solved = set()
    for s in subs:
        if s["verdict"] == "OK":
            solved.add((s["problem"]["contestId"], s["problem"]["index"]))
    candidates = []
    for p in problems:
        if "rating" not in p:
            continue
        r = p["rating"]
        if rating + 100 <= r <= 2500:
            if (p["contestId"], p["index"]) not in solved:
                candidates.append(p)
    if not candidates:
        return "Не найдено задач 😢"
    p = random.choice(candidates)
    link = f"https://codeforces.com/problemset/problem/{p['contestId']}/{p['index']}"
    return f"""
🎯 <b>Попробуй решить</b>

📌 <a href="{link}">{p['name']}</a>
⭐ Рейтинг: <b>{p['rating']}</b>


# ---------------- Команды ---------------- #

@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("👋 Бот Codeforces запущен!", reply_markup=keyboard)

@dp.message(Command("help"))
async def help_cmd(msg: types.Message):
    text = """
📜 <b>Команды бота</b>

/suggest — предложить задачу
/stats — статистика
/top — топ друзей
/solved — решено задач
/rating — рейтинг
/contest — контесты
/problem <rating> — задача по рейтингу
/compare <handle> — сравнить рейтинг
"""
    await msg.answer(text)

@dp.message(Command("suggest"))
async def suggest(msg: types.Message):
    await msg.answer(await suggest_problem())

@dp.message(Command("stats"))
async def stats(msg: types.Message):
    user = await get_user_info(MY_HANDLE)
    text = f"""
📊 <b>Статистика</b>

👤 {MY_HANDLE}
⭐ Рейтинг: {user.get("rating","нет")}
🏆 Макс: {user.get("maxRating","нет")}
🎖 Ранг: {user.get("rank","")}
"""
    await msg.answer(text)

@dp.message(Command("top"))
async def top(msg: types.Message):
    friends = await get_friends()
    users = []
    for f in friends:
        info = await get_user_info(f)
        users.append((f, info.get("rating",0)))
    users.sort(key=lambda x:x[1], reverse=True)
    text = "🏆 <b>Топ друзей</b>\n\n"
    for i,(n,r) in enumerate(users,1):
        text += f"{i}. {n} — {r}\n"
    await msg.answer(text)

@dp.message(Command("rating"))
async def rating(msg: types.Message):
    user = await get_user_info(MY_HANDLE)
    await msg.answer(f"⭐ Рейтинг {MY_HANDLE}: <b>{user.get('rating','нет')}</b>")

@dp.message(Command("solved"))
async def solved(msg: types.Message):
    subs = await get_user_submissions(MY_HANDLE)
    solved = set()
    for s in subs:
        if s["verdict"] == "OK":
            solved.add((s["problem"]["contestId"], s["problem"]["index"]))
    await msg.answer(f"✅ Решено задач: <b>{len(solved)}</b>")

@dp.message(Command("contest"))
async def contests(msg: types.Message):
    contests = await get_contests()
    upcoming = [c for c in contests if c["phase"]=="BEFORE"]
    text = "🏁 <b>Ближайшие контесты</b>\n\n"
    for c in upcoming[:5]:
        text += f"{c['name']}\n"
    await msg.answer(text)

# ---------------- кнопки ---------------- #

@dp.message(lambda m: m.text=="🎯 Предложи задачу")
async def btn1(msg: types.Message):
    await msg.answer(await suggest_problem())

@dp.message(lambda m: m.text=="📊 Моя статистика")
async def btn2(msg: types.Message):
    await stats(msg)

@dp.message(lambda m: m.text=="🏆 Топ друзей")
async def btn3(msg: types.Message):
    await top(msg)

@dp.message(lambda m: m.text=="📈 Рейтинг")
async def btn4(msg: types.Message):
    await rating(msg)

# ---------------- Keep Alive ---------------- #

async def handle(request):
    return web.Response(text="Bot alive")

async def start_web():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

# ---------------- main ---------------- #

async def main():
    asyncio.create_task(monitor_friends())
    asyncio.create_task(start_web())
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
